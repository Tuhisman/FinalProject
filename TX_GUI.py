import numpy as np
import tkinter as tk
import socket
from tkinter import ttk
from math import ceil
from scipy import ndimage
from math import sqrt
from PIL import Image
from tkinter import filedialog

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg#, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib import style

#LARGE_FONT = ("Verdana", 20)
#style.use("ggplot")

#OFDM parameters
K = 64 #OFDM subcarriers
CP = K//4  #cyclic prefix lenght of block

allCarriers = np.arange(K)  # array of carriers lenght [0-63]
guardCarriers = np.array([0, 1, 2, 3, 4 ,5 ,58, 59, 60, 61 , 62 ,63]) #guard location
dataCarriers = np.delete(allCarriers, guardCarriers) #all the remaining are data
EbN0db = 0
MyTable = 1
FinalPage = ""
Data_TT = ""

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

def SendData (Data,Settings):
    
    host = '192.168.137.1'
    port = 13000
    addr = (host, port)
    UDPSock = socket.socket (socket.AF_INET,socket.SOCK_DGRAM)
    UDPSock.sendto (Settings, addr) 
    
    for block in np.arange(Settings[1]):
        Data_Noise = AddAWGN (Data[block,:] , 1, EbN0db)
        UDPSock.sendto (Data_Noise.tostring(), addr)
        
    UDPSock.close()

def AddAWGN (OFDM_TX_Serial,N_block,EbN0bd):
    
    EsN0dB = EbN0bd + 10*np.log10(qam_order)+ 10*np.log10(K/(K+CP))
    signal_energy1 = np.mean(abs(OFDM_TX_Serial)**2)
    N0 = signal_energy1/(10**(EsN0dB/10))
    std=sqrt(N0/2)
    noise = np.random.normal(0, std, N_block*(K+CP))+1j*np.random.normal(0, std, N_block*(K+CP))

    return OFDM_TX_Serial + noise

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

def ModulationAndSend ():
    if type(Data_TT) is str :
        data_bits = String2BinArray (Data_TT)
    else:
        data_bits = Img2BitsVec (Data_TT)

    bits_reshape = data_bits.reshape(int((len(data_bits))/qam_order) ,qam_order)
    
    if (MyTable == 1):
        mapped_bits = np.array([QAM16Table[tuple(b)] for b in bits_reshape])
    else:
        mapped_bits = np.array([SpiralQAMTable[tuple(b)] for b in bits_reshape])

    N_block = ceil(len(mapped_bits)/(len(dataCarriers)))
    
    if (len(mapped_bits)%len(dataCarriers)):
        Last_Block_Lenght = len(mapped_bits)%len(dataCarriers)
    else:
        Last_Block_Lenght = len(dataCarriers)
        
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

    SettingsData_TX = np.array([MyTable,N_block,Last_Block_Lenght])
    
    SendData(OFDM_TX,SettingsData_TX)
        
class My_GUI (tk.Tk):
    
    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs)
        
        tk.Tk.wm_title (self, "Final Project Valentin Paderov")
        
        self.geometry("640x520")
        
        container = tk.Frame(self)
        container.pack(side = "top" , fill = "both" ,expand = True)
       #container.grid_rowconfigure(0, weight =1)
       # container.grid_columnconfigure(0, weight =1)
        container1 = tk.Frame(self)
        container1.pack(side = "top" , fill = "both" ,expand = True)
        
#        self.myParent = parent 
#        self.myParent.geometry("640x400")
        self.frames = {}
        
        for F in (StartPage,PageOne,PageTwo):
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
        label = tk.Label(self, text = "\n          16QAM/Spiral-QAM Transmitter          \n", font = ("Verdana", 20))
        label.pack(side = "top", pady = 25)#(row=0, column =0,padx = 0,pady=0, sticky ="nsew")
        label.config(relief ="sunken")
        
        label1 = tk.Label(self, text = "Select parameters for transmission", font = ("Verdana", 16))
        label1.pack(side = "top",)#(row=1, column =0,padx = 0,pady=0, sticky ="nsew")
        
        
        label3 = tk.Label(self, text = "Choose Eb/N0 (dB):", font = ("Verdana", 12))
        label3.pack(side = "top", fill = "both")#(row=2, column =0,padx = 0,pady=0, sticky ="nsew")
        
        def GetScale(event):
            global EbN0db
            EbN0db = scale.get()
            
            
        scale = tk.Scale(self,from_=0, to=20,orient=tk.HORIZONTAL , command = GetScale)
        scale.set(10)
        scale.pack(side = "top", fill = "none")
        

        button2 = tk.Button (self,text= "Quit", command = lambda: quitgui ())
        button2.pack(side = "bottom",anchor = "s")
        button2.config( height = 2, width = 10 )
        
        button1 = tk.Button (self,text= "Back", command = lambda: controller.show_frame(StartPage))
        button1.pack(side = "bottom",anchor = "s")
        button1.config( height = 2, width = 10 )
        
        button1 = tk.Button (self,text= "Next", command = lambda: controller.show_frame(PageOne))
        button1.pack(side = "bottom",pady=(20, 0), anchor = "s")
        button1.config( height = 2, width = 10 )
        
        
        #Buttons to choose The Constallation
        def sel():          
            global MyTable
            if (var.get() == 1):
                MyTable = 1 # for 16QAM
            else: 
                MyTable = 2 # for Spiral QAM
                
        label2 = tk.Label(self, text = "Choose constellation:", font = ("Verdana", 12))
        label2.pack(side = "top", fill = "none",anchor = "n")#(row=2, column =0,padx = 0,pady=0, sticky ="nsew")  
        
        var = tk.IntVar()
        R1 = tk.Radiobutton(self, text="16-QAM", variable=var, value=1,
                          command= lambda : sel ())
        R1.select()
        R1.pack(side = "top",fill = "none" ,anchor = "n")#(row=2, column =0,padx = 0,pady=0, sticky ="nsew") 
        
        R2 = tk.Radiobutton(self, text="Spiral QAM", variable=var, value=2,
                          command= lambda : sel ())
        R2.pack(side = "top",fill = "none",anchor = "n")#(row=2, column =0,padx = 1,pady=0, sticky ="nsew") 

        
class PageOne (tk.Frame):
    
    
    
    def __init__ (self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        #Main title
        label = tk.Label(self, text = "\n          16QAM/Spiral-QAM Transmitter          \n", font = ("Verdana", 20))
        label.pack(side = "top", pady = 25)#(row=0, column =0,padx = 0,pady=0, sticky ="nsew")
        label.config(relief ="sunken")
        
        label1 = tk.Label(self, text = "Enter text or load image you wish to transmit", font = ("Verdana", 16))
        label1.pack(side = "top",)#(row=1, column =0,padx = 0,pady=0, sticky ="nsew")
        

        
        #Get String to Send
        def GetString ():
            global Data_TT
            Data_TT = TextBox.get()
            controller.show_frame(PageTwo)
            
        def LoadImg ():
            global Data_TT
            File_dir = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("png files","*.png"),("jpeg files","*.jpg"),("all files","*.*")))
            Data_TT=Image.open(File_dir).convert("L")
            controller.show_frame(PageTwo)
            

        TextBox = tk.Entry(self, text = 'Text:', width=40, font = ("Verdana", 15))
        TextBox.pack(side = "top")
            
        button2 = tk.Button (self,text= "Load Image", command = lambda: LoadImg ())
        button2.pack(side = "top")
        button2.config( height = 2, width = 10 ) 
        


        button2 = tk.Button (self,text= "Quit", command = lambda: quitgui ())
        button2.pack(side = "bottom",anchor = "s")
        button2.config( height = 2, width = 10 )
        
        button1 = tk.Button (self,text= "Back", command = lambda: controller.show_frame(StartPage))
        button1.pack(side = "bottom",anchor = "s")
        button1.config( height = 2, width = 10 )
        
        button1 = tk.Button (self,text= "Next", command = lambda: GetString ())
        button1.pack(side = "bottom",pady=(20, 0), anchor = "s")
        button1.config( height = 2, width = 10 )
                
        
class PageTwo (tk.Frame):
    global EbN0db, MyTable
    global Flag
    global Data_TT
    
    def __init__ (self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        
        #Main title
        label = tk.Label(self, text = "\n          16QAM/Spiral-QAM Transmitter          \n", font = ("Verdana", 20))
        label.pack(side = "top", pady = 25)#(row=0, column =0,padx = 0,pady=0, sticky ="nsew")
        label.config(relief ="sunken")
        
        label1 = tk.Label(self, text = "Press 'Update' to see final parameters and then Press 'Send'", font = ("Verdana", 16))
        label1.pack(side = "top",)#(row=1, column =0,padx = 0,pady=0, sticky ="nsew")
        
        var = tk.StringVar()
        #var.set('blabla')
        
        def FinalText(var) :
            if button3 ['text'] == 'Update' :
                if type(Data_TT) is str :
                    var.set ("The parameters and data selected is:\n EbN0 = "+str(EbN0db)+"\n Constallation: "+("16QAM \n" if MyTable==1 else "SpiralQAM \n")+"The text is: " + Data_TT)
                else:
                    var.set ("The parameters and data selected is:\n EbN0 = "+str(EbN0db)+"\n Constallation: "+("16QAM \n" if MyTable==1 else "SpiralQAM \n")+"The Image is: ")
                    f = Figure (figsize = (1,1),dpi = 100)
                    plt = f.add_subplot(111)
                    plt.imshow(Data_TT, cmap='gray')
                    plt.grid(False)
                    plt.axis('off')
                    canvas = FigureCanvasTkAgg (f,self)              
                    self.widget = canvas.get_tk_widget()        
                    self.widget.pack(side = "top")
                
                button3 ['text'] ="Send"
            
            else:
                ModulationAndSend();
            
                
        label2 = tk.Label(self, textvariable = var , font = ("Verdana", 12),background= "white", anchor = "ne")
        
        label2.pack(side = "top",)#(row=1, column =0,padx = 0,pady=0, sticky ="nsew")
        label2.config(relief ="sunken")
        
        button2 = tk.Button (self,text= "Quit", command = lambda: quitgui ())
        button2.pack(side = "bottom",anchor = "s")
        button2.config( height = 2, width = 10 )
        
        button1 = tk.Button (self,text= "Back", command = lambda: controller.show_frame(PageOne))
        button1.pack(side = "bottom",anchor = "s")
        button1.config( height = 2, width = 10 )
        
        button3 = tk.Button (self,text= "Update", command = lambda: FinalText(var))
        button3.pack(side = "bottom",pady=(20, 0), anchor = "s")
        button3.config( height = 2, width = 10 )
    
        
def quitgui ():
    app.destroy()    
 
app = My_GUI()
app.mainloop()