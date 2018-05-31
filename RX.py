import numpy as np
import tkinter as tk
from tkinter import ttk
from math import ceil
from math import sqrt

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
                 
        TextBox = ttk.Entry(self, text = "Enter a Text message to send")
        TextBox.pack(side = "top")

        #Choose The Constallation
        def sel():
            global MyTable
            
            if (var.get() == 1):
                MyTable = QAM16Table
            else: 
                MyTable = SpiralQAMTable

        var = tk.IntVar()
        R1 = ttk.Radiobutton(self, text="16-QAM", variable=var, value=1,
                          command= lambda : sel ())
        R1.pack(side = "top")
        
        R2 = ttk.Radiobutton(self, text="Spiral QAM", variable=var, value=2,
                          command= lambda : sel ())
        R2.pack(side = "top")

   
        def Demodulation (data_RX,MyTable):
            
            demapping_table = {v : k for k, v in MyTable.items()}
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
            
            data_rec_reshape = data_rec.reshape(len(dataCarriers)*N_block,1)
            
            distance = abs(data_rec_reshape.reshape((-1,1)) - constellation.reshape((1,-1)))

            const_index = distance.argmin(axis=1)
            
            decision = constellation[const_index]
            
            bit_rec = np.vstack([demapping_table[C] for C in decision])
          
            # paralle -> serial
            bit_rec = bit_rec.reshape((-1,))
            
            string_rec = BinArray2String (bit_rec)
            print (string_rec)
    
app = My_GUI()
app.mainloop()
