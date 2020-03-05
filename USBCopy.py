import os
import psutil
import threading
import time
import shutil as sh
from ctypes import *
from PIL import ImageTk, Image
from tkinter import *
from tkinter.ttk import *


''' PATHS '''
iso_path = ""
img_path = ""
iso_storage = ""

# Useable drive letters for the copier to look for
# Make sure to update if using on a new computer and important drive letters are different
drives = 'A B D E F G H I J K L M N O P R T U V W X Y Z'


''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
''' Class to control the main interface of the application '''
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
class Main(Frame):
    def __init__(self, master, *args, **kwargs):
        #############################
        ### GENERIC TKINTER INITS ###
        #############################
        Frame.__init__(self, master, *args, **kwargs)
        self.style1 = Style(self)
        self.style1.configure("TButton", font=('helvetica',14))
        self.style2 = Style(self)
        self.style2.configure("TMenuButton", font=('helvetica',14))
        
        ########################
        #### SELF VARIABLES ####
        ########################
        self.drive_list = drives.split()
        self.approx_times = {"PowerDNA":"about 5 minutes", "SoloX":"20-30 minutes", "UEILogger":"less than 3 minutes", 
        "UEIOPC":"less than 3 minutes", "UEIPAC":"about 5 minutes", "UEISIM":"less than 3 minutes"}
        self.options = self.find_isos(iso_path)
        self.options.insert(0, self.options[0]) # doubled the first value because OptionMenu removes the first value for some reason

        ########################
        #### STATIC WIDGETS ####
        ########################
        # Instruction blurb
        Label(self,text="From the dropdown please select the software that needs to be copied. Then click the submit file transfer button.",\
            wraplength=350,font=("helvetica",14)).grid(column=0,row=0,columnspan=2, pady=10)
        # UEI Logo
        img = PhotoImage(file=img_path)
        logo = Label(self, image=img)
        logo.grid(row=1, column=3)
        logo.photo = img
        # ISO storage location label
        Label(self,text="Finding ISOs from {}".format(iso_storage),wraplength=400, font=('helvetica',11,'italic')).grid(column=3,row=0,pady=10,sticky=N+E)

        ##############################
        #### INTERACTABLE WIDGETS ####
        ##############################  
        # Dropdown menu
        self.menu_var = StringVar(self)
        self.menu_var.set(self.options[0])
        self.file_menu = OptionMenu(self, self.menu_var, *self.options)
        #  self.file_menu.config(font=('helvetica',16,'bold'))
        self.file_menu.grid(column=0,row=1,sticky=W,pady=30,columnspan=2)
        # Button to start copying process
        self.copy_button = Button(self, text="Begin File Transfer", command=self.precopy, style="TButton")
        self.copy_button.grid(column=1,row =1)
        # Progress bar 
        self.bar = Progressbar(self, length=300)
        self.bar.grid(row=2, column=0, columnspan=3)
        
        ########################
        #### Create the GUI ####
        ########################
        self.pack()
        self.checkForNewISOs()
   

    ''''''''''''''''''''''''''''''''''''
    '''  Methods for pop up windows  '''
    ''''''''''''''''''''''''''''''''''''
    # Window for preparing to copy files on SD(s)
    def precopy(self):                  
        try: 
            # Initialize a popup window
            self.precopy_window = Toplevel(self)

            self.iso_selected = self.menu_var.get()
            self.iso_dir = iso_path + self.iso_selected
            self.usable_drives_lbox = Listbox(self.precopy_window, font=("helvetica",14, 'bold'))
            self.usable_drives_list = []

            # Go through all possible drives (devicelist) and check for usable ones
            for dr in self.drive_list:
                path = dr + ':/'
                drive_name = dr + ':'
                if os.path.exists(path):
                    drive_size = psutil.disk_usage(drive_name).total / 2 ** 30
                    if drive_size <= 9: # If the size of the drive is less than 8 GB (helps ignore more important drives)
                        self.usable_drives_lbox.insert(END,dr)
                        self.usable_drives_list.append(dr)
            if len(self.usable_drives_list) == 0:
                self.precopy_window.destroy()
                raise InternalError("No usable drives!")

            self.precopy_window.title("Check File and Devices")
            self.iso_name = os.listdir(self.iso_dir)[0]
            self.full_iso_path = self.iso_dir + "/" + self.iso_name

            confirmation = Label(self.precopy_window, text="Please confirm the file(s) and drives below are correct. If so click okay and the file transfer will begin",wraplength = 290,font = ("helvetica",13))
            confirmation.grid(row=0, column=0, columnspan=10, pady=20, sticky=W+N)

            file_transfer = Label(self.precopy_window, text="File: {}".format(self.iso_name), font=("helvetica",16))
            file_transfer.grid(row=1, column=0)

            drives_text = Label(self.precopy_window, text="The following drives will have the file(s) copied to them: ",font = ("helvetica",14))
            drives_text.grid(row=4, column=0, stick=W)

            self.usable_drives_lbox.grid(row=5, column=0)
            
            try:
                timing_text = Label(self.precopy_window, text="With the {} ISO, it will take {}!".format(self.iso_selected, self.approx_times[self.iso_selected]), font=("helvetica",13,"bold"))
                timing_text.grid(row=6, column=0)
            except KeyError:
                pass

            self.get_files_thread = threading.Thread(target=self.getFiles)

            confirm_button = Button(self.precopy_window, text="Okay", command=lambda : [self.precopy_window.destroy(),self.get_files_thread.start()])
            confirm_button.grid(sticky=S, column=0)
        except InternalError:
            self.alert("There are no usable drives to copy to.")
        except:
            self.alert("The option selected is invalid. This directory does not exist in scope or there are no files in the named directory.\nNo files will be copied")
                                               
    # quick alert window module. used for events that only need a quick notification
    def alert(self, message):
        self.alert_window = Toplevel(self)
        self.alert_window.title("!!!!!!!!!!!")

        alert_text = Label(self.alert_window, text=message,font = ("helvetica",16))
        alert_text.pack(side='top', fill='x', pady=10)
        close_button = Button(self.alert_window, text="Okay", command=self.alert_window.destroy)
        close_button.pack()


    ''''''''''''''''''''''''''''''''''''
    ''' Methods for core operations  '''
    ''''''''''''''''''''''''''''''''''''
    # retrieves ISO file and copies to drives
    def getFiles(self):
        self.thread_list = []
        self.failed_drives = 0
        self.bar.start()
        for i in range(len(self.usable_drives_list)):
            copy_single = threading.Thread(target=self.copyIso, args=(i,))
            self.thread_list.append(copy_single)
            copy_single.start()
        while len(self.thread_list) != 0:
            time.sleep(1)
        self.bar.stop()
        if self.failed_drives == 0:
            self.alert("Copying files has completed; drives can be removed.")

    # copies the iso to the next drive in the list of drives that need to be copied to
    def copyIso(self, n):
        dr = self.usable_drives_list[n]
        if self.iso_selected == "SoloX": # If SoloX, drive needs to be formatted to NTFS
            self.format_drive(dr)

        #print("Started copying to {}:/ at {}.".format(dr, time.strftime("%H:%M:%S",time.localtime())))
        try:
            sh.copyfile(self.full_iso_path, "{}:\\{}".format(dr,self.iso_name))
            #print("Finished {}:/ at {}.".format(dr, time.strftime("%H:%M:%S",time.localtime())))
        except:
            self.failed_drives += 1
            self.alert("Ran into an error copying to drive {}:/. Please retry copying to that drive.".format(dr))
        rm = self.thread_list.pop()

    # Formats the given drive if needed for SoloX
    def format_drive(self, drive):
        path = drive + ":/"
        fm = windll.LoadLibrary('fmifs.dll')
        FMT_CB_FUNC = WINFUNCTYPE(c_int, c_int, c_int, c_void_p)
        FMIFS_HARDDISK = 0
        fm.FormatEx(c_wchar_p(path), FMIFS_HARDDISK, c_wchar_p('NTFS'),
                    c_wchar_p('SoloX Drive'), True, c_int(0), FMT_CB_FUNC(self.myFmtCallback))
    # Some helper function for format_drive (StackOverflow told me to...)
    def myFmtCallback(self, command, modifier, arg):
        #print(command)
        return 1


    ''''''''''''''''''''''''''''''''''''''''''''''''''
    ''' Methods for updating the local ISO storage '''
    ''''''''''''''''''''''''''''''''''''''''''''''''''
    # finds all available ISO folders in given dir and returns a list
    def find_isos(self, i_dir):
        dirs = os.listdir(i_dir)
        for d in dirs:
            if not d.startswith("UEI") and not d.startswith("Power") and not d.startswith("Solo"):
                dirs.remove(d)
        return dirs
    
    # checks ISO dirs stored locally to those in the shared drive location (iso_storage)
    def checkForNewISOs(self):
        local = self.find_isos(iso_path)
        shared = self.find_isos(iso_storage)
        need_to_update = []



''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
''' Container class for Main - Needed by Tkinter for organization purposes '''
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
class App(Tk):
    def __init__(self):
        Tk.__init__(self)

        self.title("UEI USB Software Copier")
        self.geometry('600x350')    

        self.main = Main(self)
        self.main.pack()

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
''' Error class that takes care of unique error throwing '''
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
class InternalError(Exception):
    pass


if __name__ == "__main__":
    app = App()
    app.mainloop()