import os
import psutil
import threading
import time
import shutil as sh
from ctypes import *
from datetime import datetime
from PIL import ImageTk, Image
from tkinter import *
from tkinter.ttk import *

from tkinterISstupid import MyOptionMenu


''' PATHS '''
iso_path = "C:/Users/edaly/Desktop/Production-pyUSB/ISOs/" #"S:/Public/!Co-op & Intern/20_1_Eoin_Daly/Production-USB/ISOs/"
img_path = "S:/R&D/Production-Software-Releases/!Source/logo.png"
iso_storage = "S:/R&D/Production-Software-Releases/"

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
        self.approx_times = {"PowerDNA":"about 5 minutes", "UEIPAC Option 11/12":"20-30 minutes", "UEILogger":"less than 3 minutes", 
        "UEIOPC":"less than 3 minutes", "PowerPC":"about 5 minutes", "UEISIM":"less than 3 minutes"}
        self.iso_dict = {} # becomes populated in findISOs
        self.options = self.findISOs(iso_path)
        self.options.insert(0, self.options[0]) # doubled the first value because OptionMenu removes the first value for some reason

        ########################
        #### STATIC WIDGETS ####
        ########################
        # Instruction blurb
        Label(self,text="Please select the software that needs to be copied from the dropdown menu, then click the file transfer button.",\
            wraplength=350,font=("helvetica",14)).grid(column=0,row=0,columnspan=2, pady=10, padx=10)
        # UEI Logo
        img = PhotoImage(file=img_path)
        logo = Label(self, image=img)
        logo.grid(row=1, column=3)
        logo.photo = img
        # ISO storage location label
        Label(self,text="Finding ISOs from {}".format(iso_storage),wraplength=400, font=('helvetica',9,'italic')).grid(column=3,row=2,pady=10, padx=10,sticky=S+E)

        ##############################
        #### INTERACTABLE WIDGETS ####
        ##############################  
        # Dropdown menu
        self.menu_var = StringVar(self)
        self.menu_var.set(self.options[0])
        self.file_menu = OptionMenu(self, self.menu_var, *self.options)
        #self.file_menu = MyOptionMenu(self, self.options[0], *self.options)
        self.file_menu.grid(column=0,row=1,pady=10, padx=10, sticky=W)
        self.file_menu['menu'].configure(font=('helvetica',(14)))

        # Button to start copying process
        self.copy_button = Button(self, text="Begin File Transfer", command=self.precopy, style="TButton")
        self.copy_button.grid(column=1,row =1, padx=10, pady=10)
        # Progress bar 
        self.bar = Progressbar(self, length=300)
        self.bar.grid(row=2, column=0, columnspan=3, pady=30, padx=30)
        # Help button
        self.help = Button(self, text="Quick Help Guide", command=self.helpMenu, style="TButton")
        self.help.grid(row=0, column=3, padx=20, pady=20, sticky=N+E)
        # Update button
        self.update_local_button = Button(self, text="Check for updates", command=self.precheck, style="TButton")
        self.update_local_button.grid(row=3, column=3, padx=20, pady=20)
        

        ########################
        #### Create the GUI ####
        ########################
        self.pack()
   

    ''''''''''''''''''''''''''''''''''''
    '''  Methods for pop up windows  '''
    ''''''''''''''''''''''''''''''''''''
    # Window for preparing to copy files on SD(s)
    def precopy(self):                  
        try: 
            # Initialize a popup window
            self.precopy_window = Toplevel(self)
            # variables
            self.iso_selected = self.menu_var.get()
            self.iso_dir = self.iso_dict[self.iso_selected]
            # list box widget that will show all the usable drives
            # (gets grid'd at the end after inserting items)
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

            # throw an error in case software cant find any usable drives
            if len(self.usable_drives_list) == 0:
                self.precopy_window.destroy()
                raise InternalError("No usable drives!")
                
            self.precopy_window.title("Check File and Devices")
            # setting variables
            self.iso_name = os.listdir(self.iso_dir)[0]
            self.full_iso_path = self.iso_dir + "/" + self.iso_name
            # Confirmation blurb
            confirmation = Label(self.precopy_window, text="Please confirm the file and drive(s) below are correct. If so, click okay and the file transfer will begin",wraplength = 290,font = ("helvetica",13))
            confirmation.grid(row=0, column=0, columnspan=10, pady=20, padx=20, sticky=W+N)
            # Print out the name of the .iso file
            file_transfer = Label(self.precopy_window, text="File: {}".format(self.iso_name), font=("helvetica",16))
            file_transfer.grid(row=1, column=0)
            # More text output things
            drives_text = Label(self.precopy_window, text="The following drives will have the file(s) copied to them: ",font = ("helvetica",14))
            drives_text.grid(row=4, column=0, stick=W)
            # placing the list box widget
            self.usable_drives_lbox.grid(row=5, column=0)
            # attempt to print out the approx time of the file transfer process
            # will fail if self.approx_times cannot find the given iso in the dictionary
            try:
                timing_text = Label(self.precopy_window, text="With the {} ISO, it will take {}!".format(self.iso_selected, self.approx_times[self.iso_selected]), font=("helvetica",13,"bold"))
                timing_text.grid(row=6, column=0)
            except KeyError:
                pass
            # Confirmation button
            self.get_files_thread = threading.Thread(target=self.getFiles)            
            confirm_button = Button(self.precopy_window, text="Okay", command=lambda : [self.precopy_window.destroy(),self.get_files_thread.start()])
            confirm_button.grid(sticky=S, column=0)
        # Error handling from above
        except InternalError:
            self.alert("There are no usable drives to copy to.")
        except:
            self.alert("The option selected is invalid. This directory does not exist in scope or there are no files in the named directory.\nNo files will be copied")
                                               
    # quick alert window module. used for events that only need a quick notification
    def alert(self, message, title="!!!!!!!!!!!"):
        self.alert_window = Toplevel(self)
        self.alert_window.title(title) 
        # displays the given message
        alert_text = Label(self.alert_window, text=message,font = ("helvetica",16))
        alert_text.pack(side='top', pady=15, padx=15)
        # Close button
        close_button = Button(self.alert_window, text="Okay", command=self.alert_window.destroy)
        close_button.pack(pady=15)
    
    # help menu pop up 
    def helpMenu(self):
        # kept insructions in a .txt in case they need to be edited later.
        with open('instructions.txt', 'r') as txt:
            lines = txt.readlines()
        
        full_text = ""
        for l in lines:
            full_text = full_text + '\n' + l
        
        self.alert(full_text, title="Help")

    ''''''''''''''''''''''''''''''''''''
    ''' Methods for core operations  '''
    ''''''''''''''''''''''''''''''''''''
    # retrieves ISO file and copies to drives
    def getFiles(self):
        self.thread_list = []
        self.failed_drives = 0
        self.bar.start()
        # starts a thread to copy to each of the drives in the usable_drives_list
        for i in range(len(self.usable_drives_list)):
            copy_single = threading.Thread(target=self.copyIso, args=(i,))
            self.thread_list.append(copy_single)
            copy_single.start()
        # loops here while waiting for threads to close
        while len(self.thread_list) != 0:
            time.sleep(1)
        self.bar.stop()
        # If any of the copying processes fail, fail_drives is increased and 
        if self.failed_drives == 0:
            self.alert("Copying files has completed; drives can be removed.")
        else:
            self.alert("Please try again with the drives that had errors\nNumber of errors: {}".format(self.failed_drives))

    # copies the iso to the next drive in the list of drives that need to be copied to
    def copyIso(self, n):
        dr = self.usable_drives_list[n]
        if self.iso_selected == "UEIPAC Option 11/12": # If SoloX, drive needs to be formatted to NTFS
            self.format_drive(dr)

        #print("Started copying to {}:/ at {}.".format(dr, time.strftime("%H:%M:%S",time.localtime())))
        try:
            sh.copy(self.full_iso_path, "{}:\\".format(dr))
            #print("Finished {}:/ at {}.".format(dr, time.strftime("%H:%M:%S",time.localtime())))
        except:
            self.failed_drives += 1
            self.alert("Ran into an error copying to drive {}:/. Please retry copying to that drive.".format(dr))
        rm = self.thread_list.pop()


    # Formats the given drive if needed for SoloX
    # Pure StackOverflow copy+paste, so just trust it :)))
    def format_drive(self, drive):
        path = drive + ":/"
        fm = windll.LoadLibrary('fmifs.dll')
        FMT_CB_FUNC = WINFUNCTYPE(c_int, c_int, c_int, c_void_p)
        FMIFS_HARDDISK = 0
        fm.FormatEx(c_wchar_p(path), FMIFS_HARDDISK, c_wchar_p('NTFS'),
                    c_wchar_p('USB Drive'), True, c_int(0), FMT_CB_FUNC(self.myFmtCallback))
    # Some helper function for format_drive (StackOverflow told me to...)
    def myFmtCallback(self, command, modifier, arg):
        #print(command)
        return 1


    ''''''''''''''''''''''''''''''''''''''''''''''''''
    ''' Methods for updating the local ISO storage '''
    ''''''''''''''''''''''''''''''''''''''''''''''''''
    # finds all available ISO folders in given dir and returns a list
    def findISOs(self, i_dir, parent_dir=""):
        dirs = os.listdir(i_dir)
        # find all subdirs (their names and path) at add to self.iso_dict
        for d in dirs:
            subdir_path = i_dir + d + '/'
            if d.startswith('!'): # If it's a source folder ("!" for exclusion)
                pass
            elif len(os.listdir(subdir_path)) == 1: # IF folder only contains iso.
                if d == "SoloX":
                    self.iso_dict["UEIPAC Option 11/12"] = subdir_path
                elif d == "PPC":
                    self.iso_dict["UEIPAC"] = subdir_path
                else:
                    self.iso_dict[d] = subdir_path
            else: # Directory has sub directories of ISO folders
                self.findISOs(subdir_path+parent_dir, "{}/".format(d))
        return list(self.iso_dict.keys())
    
    # has to remake thread everytime to prevent from getting RuntimeError of 'ThReAdS cAn OnLy bE StArTeD oNcE'
    def precheck(self):
        self.check_isos_thread = threading.Thread(target=self.checkForNewISOs)
        self.check_isos_thread.start()

    # checks ISO dirs stored locally to those in the shared drive location (iso_storage)
    def checkForNewISOs(self):
        updated=False
        
        local_iso_files = {}
        shared_iso_files = {}

        # gets full paths to all local .iso files
        self.iso_dict = {}
        local = self.findISOs(iso_path)
        for d in local:
            local_iso_files[d] = self.iso_dict[d] + os.listdir(self.iso_dict[d])[0]
        
        # gets full paths to all shared drive .iso files
        self.iso_dict = {}
        shared = self.findISOs(iso_storage)
        for d in shared:
            shared_iso_files[d] = self.iso_dict[d] + os.listdir(self.iso_dict[d])[0]        

        # two parts: add new ISOs and update existing ISOs
        # Finding and Adding new ISOs
        need_to_add = [i for i in shared if i not in local]
        self.bar.start()
        if len(need_to_add) != 0:
            updated=True
            print("need 2 copy", need_to_add)
            for d in need_to_add:
                source_dir = self.iso_dict[d]
                dest_dir = self.iso_dict[d].replace(iso_storage, iso_path)
                print("copying {} from {} to {}".format(d, source_dir, dest_dir))
                sh.copytree(source_dir, dest_dir)
        # Check if local has the most recent .iso file. If not, update and replace        
        for i in local_iso_files.keys():
            try:
                local_path = local_iso_files[i]
                shared_path = shared_iso_files[i]
                # obtain the .iso file's modification times (in UNIX time)
                local_mod_time = os.stat(local_path).st_mtime
                shared_mod_time = os.stat(shared_path).st_mtime

                if local_mod_time < shared_mod_time: # if the local has an older timestamp
                    print("updating from {} to {}".format(local_path, shared_path))
                    os.remove(local_path)
                    # copy2 keeps modification time (important bc above)
                    sh.copy2(shared_path, shared_path.replace(iso_storage, iso_path))
                    updated=True
            except KeyError:
                self.alert("There is an ISO which the local host has but the shared location does not.\nPlease see Austyn about this issue.")
            except Exception as e:
                self.alert("Error occured: {}".format(e))
        self.bar.stop()
        if updated:
            self.alert("Update finished. Please restart application")
        else:
            self.alert("Software already up to date.")




''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
''' Container class for Main - Needed by Tkinter for organization purposes '''
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
class App(Tk):
    def __init__(self):
        Tk.__init__(self)

        self.title("UEI USB Software Copier")
        #self.geometry('600x350')    

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