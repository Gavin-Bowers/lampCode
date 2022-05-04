
The original program was made by aiXander (https://github.com/aiXander/Realtime_PyAudio_FFT)
This lamp version was made by Gavin Bowers
This program was tested on Windows 10 but might work elsewhere
This is for the 15" lamp with 51 LEDs. If you have a different size, you'll need to edit the code.py and other files to replace instances of 51 or 50 with your number of LEDs

Step 1. 
	Install Python 3.10
	Look up how. The tutorial should tell you to edit the environment variables so you can access it anywhere. Make sure to do so

Step 2. 
	Install pip
	Download the installer by opening a terminal and running
		curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

	Then open a terminal in downloads and run
		python get-pip.py

Step 3. 
	Use pip to install numpy, matplotlib, scipy, pygame, and sounddevice 
	(if you have issues later, check requirements.txt for specific versions)

Step 4.
	Download Voicemeeter. It's free and you need it to use an audio output as an input to the program 
	(using voicemeeter can interact weirdly with apps like Zoom, so you may want to turn it off when not using it)

Step 5. 
	Open Voicemeeter and click the A1 "Hardware out" box in the top right. Select your preffered audio output 
	Set Voicemeeter as your computer's audio output. You should see it animate when playing audio. You can close Voicemeeter, it will run in the background

Step 6.
	Find the virtual input by running the following in python (you can open python by typing "python" into the terminal)
		import sounddevice as sd
		print(sd.query_devices())
	This will list your audio devices. Find the number for "VoiceMeeter Input (VB-Audio Voi, MME (0 in, 2 out)"

Step 7. 
	Open ls.py in a coding environment or text editor. Find 
		parser.add_argument('--device'...
	and change the default value to the number of the audio device. Save the file

Step 8. 
	Open stream_analyzer.py (in src) in a coding environment or text editor. Find 
		self.ser = serial.Serial(port='COM4'..
	and change COM4 to whichever COM port the lamp connects to
	If you don't know which, open Mu (install it if you need to) and hover the mouse over the chip icon in the bottom right (while the lamp is plugged in)

Step 9. 
	If you haven't already, connect your lamp with a data USB to micro USB male-male cable. Open the lamp's folder and copy code.py from this folder onto the lamp

Step 10.
	Close Mu if it's open as it can interfere with serial communication

Step 11. 
	Run runLightshow.bat by double clicking it

Step 12. 
	Pray
