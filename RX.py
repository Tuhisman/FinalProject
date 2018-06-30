import numpy as np
import socket
import tkinter as tk
from tkinter import ttk
from math import ceil
from math import sqrt
#import matplotlib.pyplot as plt
from PIL import Image,ImageTk 

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg#, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib import style

LARGE_FONT = ("Verdana", 8)
style.use("ggplot")

#OFDM parameters
K = 64 #OFDM subcarriers
CP = K//4  #cyclic prefix lenght of block

allCarriers = np.arange(K)  # array of carriers lenght [0-63]
guardCarriers = np.array([0, 1, 2, 3, 4 ,5 ,58, 59, 60, 61 , 62 ,63]) #guard location
dataCarriers = np.delete(allCarriers, guardCarriers) #all the remaining are data

qam_order = 4

QAM16Table = {
    (0,0,0,0) : (-3-3j),
    (0,0,0,1) : (-3-1j),
    (0,0,1,0) : (-3+3j),
    (0,0,1,1) : (-3+1j),
    (0,1,0,0) : (-1-3j),
    (0,1,0,1) : (-1-1j),
    (0,1,1,0) : (-1+3j),
    (0,1,1,1) : (-1+1j),
    (1,0,0,0) :  (3-3j),
    (1,0,0,1) :  (3-1j),
    (1,0,1,0) :  (3+3j),
    (1,0,1,1) :  (3+1j),
    (1,1,0,0) :  (1-3j),
    (1,1,0,1) :  (1-1j),
    (1,1,1,0) :  (1+3j),
    (1,1,1,1) :  (1+1j)
}

SpiralQAMTable = {
    (0,0,0,0) :  1+1j,
    (0,0,0,1) : -1+1j,
    (0,0,1,0) :  1-1j,
    (0,0,1,1) : -1-1j,
    (0,1,0,0) :  2.8j,
    (0,1,0,1) : -2.22+2.9j,
    (0,1,1,0) :  2.22-2.9j,
    (0,1,1,1) : -2.8j,
    (1,0,0,0) :  2.9+2.22j,
    (1,0,0,1) : -2.8,
    (1,0,1,0) :  2.8,
    (1,0,1,1) : -2.9-2.22j,
    (1,1,0,0) :  1.9+3.9j,
    (1,1,0,1) : -3.9+1.9j,
    (1,1,1,0) :  3.9-1.9j,
    (1,1,1,1) : -1.9-3.9j
}

def String2BinArray (string):
    temp = np.zeros(0,dtype = int)
    for c in string:
        bits = bin(ord(c))[2:]
        bits = '00000000'[len(bits):] + bits
        converted = np.fromstring(bits,'u1') - ord('0')
        temp = np.append(temp , converted)
    
    return temp

def BinArray2String (bit_array):
    bit_array_reshape = bit_array.reshape(int(len (bit_array)/8),8)
    b2i = (2**np.arange(len(bit_array_reshape[0])))
    b2i = b2i[::-1]
    result = (bit_array_reshape*b2i).sum(axis=1)
    
    return  "".join([chr(item) for item in result])

def Img2BitsVec (pic_mat):
    
    img_bit_reshape = pic_mat.reshape( len(pic_mat[0]) * len(pic_mat[0]),1 )
    temp = np.zeros(0,dtype = int)
    
    for color in img_bit_reshape:
        bits = bin(color[0])[2:]
        bits = '00000000'[len(bits):] + bits
        converted = np.fromstring(bits,'u1') - ord('0')
        temp = np.append(temp,converted)
    return temp

def BitsVec2Img(bits_vec):
    
    bit_array_reshape = bits_vec.reshape(int(len (bits_vec)/8),8)
    b2i = (2**np.arange(len(bit_array_reshape[0])))
    b2i = b2i[::-1]
    result = (bit_array_reshape*b2i).sum(axis=1)
    result_reshape = result.reshape(int(sqrt(len(result))),int(sqrt(len(result))))
    
    return result_reshape
    
class My_GUI (tk.Tk):
    
    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        
        tk.Tk.wm_title (self, "Final Project Valentin Paderov")
        
        container = tk.Frame(self)
        container.pack(side = "top" , fill = "both" ,expand = True)
        container.grid_rowconfigure(0, weight =1)
        container.grid_columnconfigure(0, weight =1)
        
        self.frames = {}
        frame = StartPage(container, self)
        self.frames[StartPage] = frame 
        frame.grid(row=0, column =0, sticky ="nsew")
        self.show_frame(StartPage)
        
    def show_frame (self,cont):
        
        frame = self.frames [cont]
        frame.tkraise()
          
class StartPage (tk.Frame):
    
    def __init__ (self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text = "Messeage Recieved is:", font = LARGE_FONT)
        label.pack(pady = 10, padx =10)
        self.widget = None

        def Demodulation (data_RX,TableIndex,NdataCarr):
            
            if (TableIndex==1):
                demapping_table = {v : k for k, v in QAM16Table.items()}
            else:
                demapping_table = {v : k for k, v in SpiralQAMTable.items()}
                
            constellation = np.array([x for x in demapping_table.keys()])
            
            N_block = ceil(len(data_RX)/(K+CP))
            
            #Serial to Paralle
            OFDM_RX_reshape = data_RX.reshape( N_block,(K+CP))
            
            #removing cycle prefix
            OFDM_noCP = OFDM_RX_reshape [:,CP:(CP+K)]
            
            #fft
            OFDM_postFFT = np.fft.fft(OFDM_noCP)
          
            #Demapping
            data_rec = OFDM_postFFT [:,dataCarriers]
#            print ('before trim' , len(data_rec))
#            print (data_rec)
#            data_rec = np.transpose(data_rec)
#            data_rec = np.trim_zeros(data_rec, 'b')
#            print ('after trim ' ,len(data_rec))
#            print (data_rec)
            data_rec_reshape = data_rec.reshape(len(dataCarriers)*N_block,1)
            
            distance = abs(data_rec_reshape.reshape((-1,1)) - constellation.reshape((1,-1)))
        
            const_index = distance.argmin(axis=1)
            
            decision = constellation[const_index]
            
            bit_rec = np.vstack([demapping_table[C] for C in decision])
          
            # paralle -> serial
            bit_rec = bit_rec.reshape((-1,))
            #print ("bits in demodulation:" , bit_rec)
#            img_rec = BitsVec2Img(bit_rec)
#            photo=ImageTk.PhotoImage(img_rec)
#            
#            f = Figure (figsize = (4,4),dpi = 100)
#            plt = f.add_subplot(111)
#            plt.imshow(photo,cmap='gray')
#            plt.grid(False)
#            canvas = FigureCanvasTkAgg (f,self)              
#            self.widget = canvas.get_tk_widget()        
#            self.widget.pack(side = "bottom" ,fill = "both")
#            
#            string_rec = BinArray2String (bit_rec)
#            print (string_rec)
#            bit_test = bit_rec1[:10]

            return bit_rec[:(NdataCarr*qam_order)]
            
        def ReceiveData()    :
            host = ""
            port = 13000
            buf = 65536
            addr = (host,port)
            UDPSock = socket.socket (socket.AF_INET,socket.SOCK_DGRAM)
            UDPSock.bind(addr)
            (settings,addr) = UDPSock.recvfrom(buf)
            settings_rec = np.fromstring(settings, dtype = int)
            #print ("setteings data:" ,settings_rec)
            #settings_rec = [mapping_table,N_block,Last_Block_Lenght]
            data_bits_rec = np.array([])
            
            for block in np.arange(settings_rec[1]):
                (data,addr) = UDPSock.recvfrom(buf)
                data_rec = np.fromstring(data, dtype = complex)
                #print ("data:" ,data_rec)
                if (block!=(settings_rec[1]-1)):
                    temp_data = Demodulation (data_rec,settings_rec[0],52)
                    #print ("temp_data: " ,temp_data)
                else:
                    temp_data = Demodulation (data_rec,settings_rec[0],settings_rec[2])
                    #print ("temp_data: " ,temp_data)
                
                data_bits_rec = np.append(data_bits_rec , temp_data)
                
            UDPSock.close()
            
            data_bits_rec = data_bits_rec.astype(int)
            #print ("data bits:" ,data_bits_rec)
            
            if (settings_rec[1]<20):
                message = BinArray2String (data_bits_rec)
                TextBox.insert (0.0 , message)
            else:
                photo = BitsVec2Img(data_bits_rec)
                #print (img_rec)
                #photo=ImageTk.PhotoImage(Image.fromarray(img_rec,"L"))
                #print (img_rec)
                f = Figure (figsize = (4,4),dpi = 100)
                plt = f.add_subplot(111)
                plt.imshow(photo,cmap='gray')
                plt.grid(False)
                plt.axis('off')
                canvas = FigureCanvasTkAgg (f,self)              
                self.widget = canvas.get_tk_widget()        
                self.widget.pack(side = "bottom" ,fill = "both")
                
                
        #Choose The Constallation
#        def sel():
#            global MyTable
#            
#            if (var.get() == 1):
#                MyTable = QAM16Table
#            else: 
#                MyTable = SpiralQAMTable
#
#        var = tk.IntVar()
#        R1 = ttk.Radiobutton(self, text="16-QAM", variable=var, value=1,
#                          command= lambda : sel ())
#        R1.pack(side = "top")
#        
#        R2 = ttk.Radiobutton(self, text="Spiral QAM", variable=var, value=2,
#                          command= lambda : sel ())
#        R2.pack(side = "top")
        
        SendButton = ttk.Button(self,text= "Press to Listen", 
                            command = lambda: ReceiveData())
        SendButton.pack(side = "top")
        
        TextBox = tk.Text (self, width =35 , height = 5)
        TextBox.pack(side = "top")
        


app = My_GUI()
app.mainloop()
