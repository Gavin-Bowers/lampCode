
Audio visualizer from aiXander (https://github.com/aiXander/Realtime_PyAudio_FFT)

Lamp code from Nick Ruffalo (https://github.com/nruffilo/BitsnBots/blob/master/CrystalLamp/code.py)

This lamp version was made by Gavin Bowers

This program was tested on Windows 10 but might work elsewhere

Step 1. 
	Install Python 3.10. Look up how if you need to. The tutorial should tell you to edit the environment variables so you can access it anywhere. Make sure to do so

Step 2. 
	Install pip
	Download the installer by opening a terminal and running
		
		curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

Then open a terminal in downloads and run
	
		python get-pip.py

Step 3. 
	Use pip to install numpy, matplotlib, scipy, pygame, pySerial, and sounddevice 
	(if you have issues later, check requirements.txt for specific versions)

Step 4.
	Download Voicemeeter. It's free and you need it to use an audio output as an input to the program 
	(Using voicemeeter can interact weirdly with apps like Zoom, so you may want to turn it off when not using it)
	(Any audio mirroring program that can create a virtual input from output will work)

Step 5. 
	Open Voicemeeter and click the A1 "Hardware out" box in the top right. Select your preferred audio output 
	Set Voicemeeter as your computer's audio output. You should see it animate when playing audio. You can close Voicemeeter, it will run in the background

Step 6.
	Find the virtual input by running the following in python (you can open python by typing "python" into the terminal)
		
		import sounddevice as sd
		print(sd.query_devices())

This will list your audio devices. Find the number for "VoiceMeeter Input (VB-Audio Voi, MME (0 in, 2 out)"

Step 7. 
	Edit runLightshow.bat. If you can't edit it, rename it to runLightshow.txt and edit it, then revert it afterwards.
	Change the --device value to the number of your virtual audio device.
	Change the port value to whichever serial port your lamp connects to.
	If you don't know which, open Mu (install it if you need to, select circuitpython as the language) and hover the mouse over the chip icon in the bottom right while the lamp is plugged in
	

Step 8.
	Edit code.py and change pixelCount to your number of LEDs (34 for smaller lamps). Probably set buffer to 0. Also change the pins (marked with <--) to the 	  correct ones for your device.
Step 9. 
	If you haven't already, connect your lamp with a data USB to micro USB male-male cable. Open the lamp's folder and copy code.py from this folder onto the lamp.
	If the device's folder doesn't have neopixel.mpy, add it from this folder.

Step 10.
	Close Mu if it's open as it can interfere with serial communication

Step 12. 
	Run runLightshow.bat by double clicking it
