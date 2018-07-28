import numpy as np
import socket
import tkinter as tk
from tkinter import ttk
from math import ceil
from math import sqrt
#import matplotlib.pyplot as plt
from PIL import Image#,ImageTk 
from math import pi
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

Data_RR_Noise = ""
Data_RR_Refrence = ""
MyTable = 1
DataType = 1
DataWNoise = np.array([])
PhaseNoise = 0

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
    global PhaseNoise
    if PhaseNoise:
        noise_ph= np.random.normal(0 ,PhaseNoise*(pi/180) , len(OFDM_postFFT))
        OFDM_postFFT = OFDM_postFFT*np.exp(1j*noise_ph)
    
    #Demapping
    data_rec = OFDM_postFFT [:,dataCarriers]
        
    data_rec_reshape = data_rec.reshape(len(dataCarriers)*N_block,1)
    
    global DataWNoise
    DataWNoise = np.append(DataWNoise , data_rec_reshape[:NdataCarr])
        
    distance = abs(data_rec_reshape.reshape((-1,1)) - constellation.reshape((1,-1)))

    const_index = distance.argmin(axis=1)
    
    decision = constellation[const_index]
    
    bit_rec = np.vstack([demapping_table[C] for C in decision])
  
    # paralle -> serial
    bit_rec = bit_rec.reshape((-1,))

    return bit_rec[:(NdataCarr*qam_order)]


def ReceiveData():
    
    host = ""
    port = 13000
    buf = 65536
    addr = (host,port)
    UDPSock = socket.socket (socket.AF_INET,socket.SOCK_DGRAM)
    UDPSock.bind(addr)
    (settings,addr) = UDPSock.recvfrom(buf)
    settings_rec = np.fromstring(settings, dtype = int) 
    #settings_rec = [mapping_table,N_block,Last_Block_Lenght,DataType,PhaseNoise]
    
    global MyTable
    MyTable = settings_rec[0]
    global DataType
    DataType = settings_rec[3]
    global PhaseNoise
    PhaseNoise = 0
    
    data_bits_rec = np.array([])

    for block in np.arange(settings_rec[1]):
        (data,addr) = UDPSock.recvfrom(buf)
        data_rec = np.fromstring(data, dtype = complex)
        
        if (block!=(settings_rec[1]-1)):
            temp_data = Demodulation (data_rec,MyTable,52)
        else:
            temp_data = Demodulation (data_rec,MyTable,settings_rec[2])

        data_bits_rec = np.append(data_bits_rec , temp_data)

    global Data_RR_Refrence
    Data_RR_Refrence = data_bits_rec.astype(int)

    data_bits_rec = np.array([])
    PhaseNoise = settings_rec[4]
    global DataWNoise
    DataWNoise = np.array([])
    
    for block in np.arange(settings_rec[1]):
        (data,addr) = UDPSock.recvfrom(buf)
        data_rec = np.fromstring(data, dtype = complex)
        
        if (block!=(settings_rec[1]-1)):
            temp_data = Demodulation (data_rec,MyTable,52)
        else:
            temp_data = Demodulation (data_rec,MyTable,settings_rec[2])

        data_bits_rec = np.append(data_bits_rec , temp_data)
        
    UDPSock.close()
    
    global Data_RR_Noise
    Data_RR_Noise = data_bits_rec.astype(int)
        
class My_GUI (tk.Tk):
    
    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        
        tk.Tk.wm_title (self, "Final Project Valentin Paderov")
        
        self.geometry("640x620")
        
        container = tk.Frame(self)
        container.pack(side = "top" , fill = "both" ,expand = True)
       #container.grid_rowconfigure(0, weight =1)
       # container.grid_columnconfigure(0, weight =1)
        container1 = tk.Frame(self)
        container1.pack(side = "top" , fill = "both" ,expand = True)
        
#        self.myParent = parent 
#        self.myParent.geometry("640x400")
        self.frames = {}
        
        for F in (StartPage,PageOne):
            frame = F(container,self)
            self.frames[F] = frame 
            frame.grid(row=0, column =0, sticky ="nsew")
        
        self.show_frame(StartPage)
        
    def show_frame (self,cont):
        
        frame = self.frames [cont]
        frame.tkraise()
       
class StartPage (tk.Frame):
    
    
    def __init__ (self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        
        #Main title
        label = tk.Label(self, text = "\n          16QAM/Spiral-QAM Receiver          \n", font = ("Verdana", 20))
        label.pack(side = "top", pady = 25)#(row=0, column =0,padx = 0,pady=0, sticky ="nsew")
        label.config(relief ="sunken")
        
        label1 = tk.Label(self, text = "Press 'Start Listen' to begin", font = ("Verdana", 16))
        label1.pack(side = "top",)#(row=1, column =0,padx = 0,pady=0, sticky ="nsew")
        
        def ListenChannel ():
            ReceiveData()
            controller.show_frame(PageOne)

        button2 = tk.Button (self,text= "Quit", command = lambda: quitgui ())
        button2.pack(side = "bottom",anchor = "s")
        button2.config( height = 2, width = 10 )
        
#        button1 = tk.Button (self,text= "Back", command = lambda: controller.show_frame(StartPage))
#        button1.pack(side = "bottom",anchor = "s")
#        button1.config( height = 2, width = 10 )
        
        button1 = tk.Button (self,text= "Start Listen", command = lambda: ListenChannel())
        button1.pack(side = "bottom",pady=(200, 0), anchor = "s")
        button1.config( height = 2, width = 10 )
        


        
class PageOne (tk.Frame):

    def __init__ (self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        

        #Main title
        label = tk.Label(self, text = "\n          16QAM/Spiral-QAM Reciever          \n", font = ("Verdana", 20))
        label.pack(side = "top", pady = 0)#(row=0, column =0,padx = 0,pady=0, sticky ="nsew")
        label.config(relief ="sunken")
        
        label1 = tk.Label(self, text = "Press 'Update' to load Data", font = ("Verdana", 16))
        label1.pack(side = "top",)#(row=1, column =0,padx = 0,pady=0, sticky ="nsew")
        
        nb = ttk.Notebook(self, width = 300 ,height = 300)
        page1 = ttk.Frame(nb)
        page2 = ttk.Frame(nb)
        page3 = ttk.Frame(nb)
        page4 = ttk.Frame(nb)
        nb.add(page1, text='Data Recieved')
        nb.add(page2, text='Constallation')
        nb.add(page3, text='Signal + Noise')
        nb.add(page4, text='Statistics')
        nb.pack(expand=1, fill="y")
        
        def UpdateData():
            global Data_RR_Noise
            global Data_RR_Refrence
            BadBits =np.sum(Data_RR_Refrence^Data_RR_Noise)
            BER = BadBits/len(Data_RR_Refrence)
            
            #Constallation
            global MyTable
            f = Figure (figsize = (3,3),dpi = 100)
            plt = f.add_subplot(111)    
            
            for b3 in [0, 1]:
                for b2 in [0, 1]:
                    for b1 in [0, 1]:
                        for b0 in [0, 1]:
                            B = (b3, b2, b1, b0)
                            if MyTable == 1 :
                                Q = QAM16Table[B]
                            else:
                                Q = SpiralQAMTable[B]
                            plt.plot(Q.real, Q.imag, 'bo')
                            plt.text(Q.real, Q.imag+0.2, "".join(str(x) for x in B), ha='center')
                            
            plt.plot([-5,5], [0 ,0],'b')
            plt.plot([0 ,0], [-5,5],'b')
            plt.grid(True)
            plt.set_xlim(-5, 5)
            plt.set_ylim(-5, 5)
#            plt.set_xlabel('Real part (I)') 
#            plt.set_ylabel('Imaginary part (Q)')                  
            canvas = FigureCanvasTkAgg (f,page2)              
            page2.widget = canvas.get_tk_widget()        
            page2.widget.pack(side = "top",fill = "both") 
            
            #Modulated Data

            if (DataType == 1):
                TextBox = tk.Text (page1)#, width =35 , height = 5)
                TextBox.pack(side = "top",fill = "both")
                message_noise = BinArray2String (Data_RR_Noise)
                TextBox.insert (0.0 , message_noise)
            else:
                photo = BitsVec2Img(Data_RR_Noise)
                f = Figure (figsize = (3,3),dpi = 100)
                plt = f.add_subplot(111)
                plt.imshow(photo,cmap='gray')
                plt.grid(False)
                plt.axis('off')
                canvas = FigureCanvasTkAgg (f,page1)              
                page1.widget = canvas.get_tk_widget()        
                page1.widget.pack(side = "bottom" ,fill = "both")            
            
            #Signal+Noise
            global DataWNoise
            f = Figure (figsize = (3,3),dpi = 100)
            plt = f.add_subplot(111)
            plt.plot(DataWNoise.real, DataWNoise.imag, 'bo')
            for b3 in [0, 1]:
                for b2 in [0, 1]:
                    for b1 in [0, 1]:
                        for b0 in [0, 1]:
                            B = (b3, b2, b1, b0)
                            if MyTable == 1 :
                                Q = QAM16Table[B]
                            else:
                                Q = SpiralQAMTable[B]
                            plt.plot(Q.real, Q.imag, 'ro')
#            plt.set_xlim(-2, 2)
#            plt.set_ylim(-2, 2)
#            plt.set_xlabel('Real part (I)') 
#            plt.set_ylabel('Imaginary part (Q)')          
            plt.grid(True)
            canvas = FigureCanvasTkAgg (f,page3)              
            page3.widget = canvas.get_tk_widget()        
            page3.widget.pack(side = "top",fill = "both")
            
            #Data No Noise

            if (DataType == 1):
                TextBox = tk.Text (page4)#, width =35 , height = 5)
                TextBox.pack(side = "top",fill = "both")
                message_no_noise = BinArray2String (Data_RR_Refrence)
                toprint = "Text recieved without noise:\n"+message_no_noise+"\n\nText recieved with noise:\n"+message_noise
                toprint = toprint+"\n\nThere is "+str(BadBits)+" wrong bits\nBER is: "+str(BER)
                TextBox.insert (0.0 ,toprint) 
            else:
                photo = BitsVec2Img(Data_RR_Refrence)
                f = Figure (figsize = (2,2),dpi = 100)
                plt = f.add_subplot(111)
                plt.imshow(photo,cmap='gray')
                plt.grid(False)
                plt.axis('off')
                canvas = FigureCanvasTkAgg (f,page4)              
                page4.widget = canvas.get_tk_widget()        
                page4.widget.pack(side = "bottom" ,fill = "both")
                TextBox = tk.Text (page4)#, width =35 , height = 5)
                TextBox.pack(side = "top",fill = "both")
                toprint = "There is "+str(BadBits)+" wrong bits\nBER is: "+str(BER)+"\nImage recieved without noise:"
                TextBox.insert (0.0 ,toprint) 
            
            

            
        button2 = tk.Button (self,text= "Quit", command = lambda: quitgui ())
        button2.pack(side = "bottom",anchor = "s")
        button2.config( height = 2, width = 10 )
        
#        button1 = tk.Button (self,text= "Back", command = lambda: controller.show_frame(StartPage))
#        button1.pack(side = "bottom",anchor = "s")
#        button1.config( height = 2, width = 10 )
        
        button1 = tk.Button (self,text= "Update", command = lambda: UpdateData())
        button1.pack(side = "bottom",pady=(20, 0), anchor = "s")
        button1.config( height = 2, width = 10 )

def quitgui ():
    app.destroy()    
 
app = My_GUI()
app.mainloop()
