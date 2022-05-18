
Audio visualizer from aiXander (https://github.com/aiXander/Realtime_PyAudio_FFT)
Original lamp code from Nick Ruffalo (https://github.com/nruffilo/BitsnBots/blob/master/CrystalLamp/code.py)
This project by Gavin Bowers

For Windows 10

Download Voicemeeter. You need it to mirror audio for the program, although any program that can mirror output to a a virtual input will work.
Open Voicemeeter and click the A1 "Hardware out" box in the top right. Select your preferred audio output.
Set Voicemeeter as your computer's audio output. You should see it animate when playing audio. Yes, this means you can't easily change your volume. The windows sound device list can do it, as well as voicemeeter's UI. Using voicemeeter can interact weirdly with apps like Zoom, so you may want to turn it off when not using it. Voicemeeter can be set to run in the background when closed.

The following step is used to find your audio device ids because I don't know a better way. Python is no longer a dependancy of the application.
Install Python 3 with the installer. Then use the following command line commands to install pip and sounddevice, then find your audio devices.
		
	curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
	python get-pip.py
	pip install sounddevice
	python
	import sounddevice as sd
	print(sd.query_devices())

This will list your audio devices. Find the number for "VoiceMeeter Input (VB-Audio Voi, MME (0 in, 2 out)"

Edit the link file by right clicking, selecting properties, and changing the arguments in the "target" field.
Change the --device value to the number of the virtual audio device you found in the last step.
Change the --port value to whichever serial port your lamp connects to.
If you don't know which, open Mu (install it if you need to, select circuitpython as the language) and hover the mouse over the chip icon in the bottom right while the lamp is plugged in
Change the --n_frequency_bins number to half the number of leds on your lamp
Optionally, you can change the --window_size and --smoothing_length values. Increasing these will make the lightshow smoother but less responsive. They don't have to be the same.
	
Edit code.py and change smallLamp to True if you have a 34 LED lamp. If your lamp has different ports and/or number of LEDs from either preset, alter the smallLamp preset to have the correct ports and N_PIXELS. If you have LEDs sticking out from under your crystal, you may want to increase BUFFER. If your device bugs out without the audio setup, you may need to copy it over from my preset.

If you haven't already, connect your lamp with a data USB to micro USB male to male cable. Open the lamp's folder and copy code.py from this folder onto the lamp.
If the device's folder doesn't have neopixel.mpy, add it from this repository or from the adafruit website.

You can move the link wherever you want, and use it to run the program. Make sure Mu's serial isn't opened or it will crash. It will also crash if the port argument is wrong or if the lamp isn't plugged in.

Lamp controls:

Single click: decrease brightness by 20%, loops back to 100% after off
Long click: changes color scheme, loops.
Double click: changes lightshow mode, currently only audio visualizer and fire. Loops. Resets color scheme.
