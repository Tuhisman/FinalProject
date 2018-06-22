import numpy as np
import tkinter as tk
import socket
from tkinter import ttk
from math import ceil
from scipy import ndimage
from math import sqrt
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

def SendData (Data,Settings,Noise):
    
    host = '192.168.137.1'
    port = 13000
    addr = (host, port)
    UDPSock = socket.socket (socket.AF_INET,socket.SOCK_DGRAM)
    UDPSock.sendto (Settings, addr) 
    
    for block in np.arange(Settings[1]):
        Data_Noise = AddAWGN (Data[block,:] , 1, Noise)
        UDPSock.sendto (Data_Noise.tostring(), addr)
        
    UDPSock.close()

def AddAWGN (OFDM_TX_Serial,N_block,EbN0bd):
    
    EsN0dB = EbN0bd + 10*np.log10(qam_order)+ 10*np.log10(K/(K+CP))
    signal_energy1 = np.mean(abs(OFDM_TX_Serial)**2)
    N0 = signal_energy1/(10**(EsN0dB/10))
    std=sqrt(N0/2)
    noise = np.random.normal(0, std, N_block*(K+CP))+1j*np.random.normal(0, std, N_block*(K+CP))

    return OFDM_TX_Serial #+ noise

def Img2BitsVec (pic_mat):
    pic_mat = np.array (pic_mat)
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
        label = tk.Label(self, text = "Enter message to send:", font = LARGE_FONT)
        label.pack(side = "top" ,fill = "both")#(pady = 10, padx =10)
        self.widget = None
        
        #Display Empty Graph
        def InitiateGraph():
            f = Figure (figsize = (4,4),dpi = 100)
            plt = f.add_subplot(111)  
            plt.plot([-4.5,4.5], [0 ,0],'b')
            plt.plot([0 ,0], [-4.5,4.5],'b')
            plt.grid(True)
            canvas = FigureCanvasTkAgg (f,self) 
            self.widget = canvas.get_tk_widget()        
            self.widget.pack(side = "bottom" ,fill = "both")
        
        InitiateGraph()
            
        #Display The Graph
        def DisplayConstalation (table):
            
            if self.widget:
                self.widget.destroy()
                
            f = Figure (figsize = (4,4),dpi = 100)
            plt = f.add_subplot(111)    
            
            for b3 in [0, 1]:
                for b2 in [0, 1]:
                    for b1 in [0, 1]:
                        for b0 in [0, 1]:
                            B = (b3, b2, b1, b0)
                            Q = table[B]
                            plt.plot(Q.real, Q.imag, 'bo')
                            plt.text(Q.real, Q.imag+0.2, "".join(str(x) for x in B), ha='center')
                            
            plt.plot([-4.5,4.5], [0 ,0],'b')
            plt.plot([0 ,0], [-4.5,4.5],'b')
            plt.grid(True)
            
            canvas = FigureCanvasTkAgg (f,self)              
            self.widget = canvas.get_tk_widget()        
            self.widget.pack(side = "bottom" ,fill = "both")
        
        #Get String to Send
        def GetString ():
            MyString = TextBox.get()
            if MyString:
                ModulationAndSend (MyString, MyTable)
            else:
                TextBox.insert(1,"Enter message here")
                
            
        TextBox = ttk.Entry(self, text = "Enter a Text message to send")
        TextBox.pack(side = "top")

        SendButton = ttk.Button(self,text= "Send", 
                            command = lambda: GetString())
        SendButton.pack(side = "top")
        
        #Choose The Constallation
        def sel():
            global MyTable
            
            if (var.get() == 1):
                MyTable = 1 # for 16QAM
                DisplayConstalation(QAM16Table)
            else: 
                MyTable = 2 # for Spiral QAM
                DisplayConstalation(SpiralQAMTable)

            #DisplayConstalation(MyTable)

        var = tk.IntVar()
        R1 = ttk.Radiobutton(self, text="16-QAM", variable=var, value=1,
                          command= lambda : sel ())
        R1.pack(side = "top")
        
        R2 = ttk.Radiobutton(self, text="Spiral QAM", variable=var, value=2,
                          command= lambda : sel ())
        R2.pack(side = "top")

   
        def ModulationAndSend (MyString, mapping_table):
            #pic_mat=Image.open("pi40.png").convert("L")
            #data_bits = Img2BitsVec (pic_mat)
            
            data_bits = String2BinArray (MyString)
            
            bits_reshape = data_bits.reshape(int((len(data_bits))/qam_order) ,qam_order)
            
            if (mapping_table == 1):
                mapped_bits = np.array([QAM16Table[tuple(b)] for b in bits_reshape])
            else:
                mapped_bits = np.array([SpiralQAMTable[tuple(b)] for b in bits_reshape])
                
            print ("mapped_bits",  len(mapped_bits))
            
            N_block = ceil(len(mapped_bits)/(len(dataCarriers)))
            Last_Block_Lenght = len(mapped_bits)%len(dataCarriers)
            
            print ("N_block",  N_block)
            print ("dataCarriers",  len(mapped_bits)%len(dataCarriers))
            if (len(mapped_bits)%len(dataCarriers))!= 0 :
                mapped_bits = np.append(mapped_bits, np.zeros((len(dataCarriers)-(len(mapped_bits)%len(dataCarriers))),dtype = complex))
                
            mapped_bits_reshape = mapped_bits.reshape(N_block, len(dataCarriers))
            
            OFDM_blocks = np.zeros((N_block,K), dtype = complex)
            OFDM_blocks [:,dataCarriers] = mapped_bits_reshape
            
            #ifft
            OFDM_ifft = np.fft.ifft(OFDM_blocks)
            
            #adding cycle prefix
            CP_values = OFDM_ifft[:,K-CP:K]
            OFDM_TX = np.concatenate((CP_values, OFDM_ifft), axis=1)
#            print ("OFDM_TX",  OFDM_TX.shape)
#            print ("OFDM_TX[0]",  OFDM_TX[0,:], "LENGHt" , len (OFDM_TX[0,:]))
#            print ("OFDM_TX[1]",  OFDM_TX[1,:], "LENGHt" , len (OFDM_TX[1,:]))
            
            #Paralle to Serial
          #  OFDM_TX_Serial = OFDM_TX.reshape ( 1, (K+CP)*N_block)
           # print ("OFDM_TX_Serial",  OFDM_TX_Serial.shape)
            EbN0db = 5
            
           # OFDM_Noise = AddAWGN (OFDM_TX_Serial , N_block, EbN0db)
           # print ("OFDM_Noise",  OFDM_Noise.shape)
            
           # Data_TX = OFDM_Noise.tostring()
           # print ("Data_TX",  len (Data_TX))
            
            SettingsData_TX = np.array([mapping_table,N_block,Last_Block_Lenght])#.tostring()
            
            SendData(OFDM_TX,SettingsData_TX,EbN0db)
            
            
app = My_GUI()
app.mainloop()
