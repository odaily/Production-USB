# SD Card Copying Software
>*Created by Eoin Daly -- daly.e@husky.neu.edu*

This program was made to help everyone's favorite Ray of Sunshine. This enables the copying of a single (or multiple, though that seems impractical) ISO image file to multiple USB devices at once.

This was written using the tkinter library, along with a number of other python modules to help with multithreading, file copying, and path handling and built with the PyInstaller package.

Further details about the application's functionality and possible additions can be found below.

## Getting Started
---
This application should be run with some version of Python 3. A requirements.txt is provided as well for pip installs (to install off of a requirements.txt, run `pip install -r requirements.txt`). Before running, make sure all the path variables are set correctly (more details can be found in the __Variables__ section).

To compile into an executable, use PyInstaller as `pyinstaller -wF USBCopy.py`. If a certain icon is desired and available, PyInstaller could be run instead as `pyinstaller -wF -i ${ICON_PATH} USBCopy.py`.
> PyInstaller Flags:\
> __-w__: Has executable launch without a terminal open behind it.\
> __-F__: Bundles executable to be only one file.\
> __-i FILE.ico__: Set the icon of the executable to be the icon specified.

## Core Operation
---
Once the application is opened, the user is greeted with a GUI with simple instructions on how to select an ISO and begin copying. Once the "Begin File Transfer" button is pressed, the program searches for drives it can copy to. Currently, it is fitted to only look for drives that are non-essential (so no C:/ or S:/) and less that 8 GB in total size. If no drives are found, an error message is returned. 

If there are usable drives, a confimation window appears, listing all the drives to be copied to along with the ISO file name and an approximate time if recorded.
Pressing okay will close the confirmation window and a loading bar animation will start on the original GUI.
Once copying is completed, the loading bar stops and the user is alerted with another window popup that file transfer has been completed. 

### Variables
---
Certian variables are located at the top of the source code and are easy to change to help flexibility of the program. The following are a list of the important variables a future maintainer should be aware of if trying to edit the code.

* `iso_path`: This is a variable set to be the path of a directory on the host computer that contains all the ISO image folders.
* `img_path`: This is set to be the path of the UEI logo that is displayed in the main GUI. This could be on the shared drive, though it is preferred to be stored locally to ensure existence.
* `iso_storage`: This is the location *__on the shared drive__* where new ISO image folders will be added to. 
* `drives`: A list of all drives the program is allowed to check. Currently, C and S have been removed, so any new important drives that are located on the host should be removed from this list.
* `approx_times`: An attribute of the Main tkinter class. This is a dictionary that contains an approximate measure of the time needed to copy a specific ISO image. If a new image is added, it's name and approximate time should be added to this dictionary. Timing can be checked by using the provided `copyTime_SH.py` script (exchanging path variables) and running `time python copyTime_SH.py`. The program has error checking in place such that it can run without an approximate time, but it would be nice to have.


### Multithreading
---
The application uses the python threading module to assist in faster copying to multiple devices. Because certain ISO images can take a long time to copy, it was decided that starting a thread to take care of copying to the different drives was much faster. 

### File Copying
---
This application uses the shutil module for file copying. Each ISO is individually copied using the `shutil.copyfile()` function. This proved to be the fastest (and simplest) method of copying to FAT32 drives. 
__Note:__ Copying to NTFS drives is a bit slower, but not enough to consider changing the method used. 

### Adding New ISOs
---
To add a new ISO image for the application to be able to use, place it in a folder named whatever your ISO image is named (something simple to help easier finding). Then place this into whatever path the `iso_storage` is set to. The program will automatically check to see if it has the latest versions of every locally stored ISO as well as new ISOs in the `iso_storage`. If needed, it will update the local directory of ISOs upon startup. 

### Adding Additional Popups
---
If new extensions to the application need some new popup windows, the implementation is very simple. __Note:__ If a popup requiring no more functionality than a popup to display a message and the user closes it anyway, use the `alert()` method of the Main class. 
To create a new popup, use the tkinter class `Toplevel()`. `Toplevel()` takes an argument for a master. In this case, the master should be the Main class, so if the popup is within a method for the Main class, a popup can be instatiated by saying `Toplevel(self)`. When creating widgets for this popup window, be sure to set their master to be your popup and not the Main.