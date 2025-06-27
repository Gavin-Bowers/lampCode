### Credits
Audio visualizer adapted from [aiXander's project](https://github.com/aiXander/Realtime_PyAudio_FFT)\
[Original lamp code](https://github.com/nruffilo/BitsnBots/blob/master/CrystalLamp/code.py) from Nick Ruffalo

### Setup
* Connect the lamp to your computer with a micro-USB to USB cable. Make sure the cable isn't power-only
* If the connection is successful, the device should show up as a drive, e.g. `USB Drive (E:)`
* Copy the contents of `pico_code` onto the device. It will automatically reboot and run the code

### Building
* Install Nuitka with `pip install nuitka`
* Build with `python -m nuitka --enable-plugin=pyqt6 --include-package=scipy._cyutility --mode=onefile --windows-console-mode=disable --product-name="Lamp Controller" --windows-icon-from-ico=resources/icon.ico --file-version=1.0.0 .\src\app.py`

### Lamp controls
| Button Input | Setting               |
|--------------|-----------------------|
| Short press  | Change brightness     |
| Long press   | Change color scheme   |
| Double press | Change lightshow mode |

