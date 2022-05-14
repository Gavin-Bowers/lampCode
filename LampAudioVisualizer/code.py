#Imports
import supervisor
import board
import neopixel #If missing, download adafruit circuitpython 6.X bundle and move neopixel.mpy into the drive for this device. Now bundled with this program
import time
from digitalio import DigitalInOut, Direction, Pull
import analogio
import audiobusio
import audiocore
import random
import array
import math
import random
import array

#Setup

#Audio (audio isn't actually supported, it just bugs out on my device without this)
mic = audiobusio.PDMIn(clock_pin=board.GP3, data_pin=board.GP2,mono=True, sample_rate=16000, bit_depth=16)

#Button Setup
btn = DigitalInOut(board.GP9) #GP2 for smaller lamps <--
btn.direction = Direction.INPUT
btn.pull = Pull.UP

#Led Setup
pixelCount = 51 #Number of LEDs. 34 for smaller lamps <--
buffer = 1 #The number of pixels you don't want to use at the start of the strip. Probably should be 0
half = math.floor((pixelCount-buffer)/2.0) #If the (pixelCount - buffer) is odd, stuff might break
pixels = neopixel.NeoPixel(board.GP5, pixelCount, brightness=1, auto_write=False) #GP0 for smaller lamps <--

#Parameters (now in one convenient location)

#General
pressed = False #Button value
dcWait = 0 #Double Click timer
animationMode = 0 #Which animation is displaying
brightness = 1 #LED Brightness
brIncrement = 0.2 #Amount the brightness changes per button press. 0 to 1. default 0.2

#Audio Visualizer Parameters
downtime = 0 #no touch
scroll = 0.0 #no touch
scrollSpeed = 3.0 #Scroll speed. Default is 1
chroma = 0.02 #Factor of the raw color value. Default is 0.01
whiteness = 0.1 #Factor of the value added to each color. Default is 0.15
maxVal = 255 #Max R/G/B value. Setting this above 255 allows for inverted colors by wrapping around
rainbowness = 1.0 #How many colors to display at once. Works if greater than 0, but the reasonable range is from 1 to 10. 80 is fun
blending = 1 #How blended the colors are. Default is 0.5. Works reasonably from 0 to 2

#Fire Parameters and setup
smoothing = 0.01 #Flame smoothing
flamePixels = []
for i in range(pixelCount):
    flamePixels.append([0,0,0,0]) #hue, brightness, Flicker speed, Flicker direction

#Utilities

def wheel(pos):
    #kind of stinky. Only used by fire animation now
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

#Modes:

def audioVis(hasData):
    global half, buffer, scroll, scrollSpeed, chroma, rainbowness, whiteness
    scrollJuice = 0.0
    pixels.fill((0,0,0))
    if hasData:
        value = bytes(input(), 'utf-8')
        temp = value.strip(b' ')
        lightshow = temp.split(b' ')
        val = 0.0
    for i in range(half):
        if hasData:
            try:
                val = min(100.0,float(lightshow[min(i,len(lightshow)-1)]))
            except ValueError:
                val = 0
        else:
            val = 0
        scrollJuice += min(0.0002 * math.pow(val,2),2)
        x = i - scroll
        w = (3/4) * (20 / rainbowness)
        r = (20 / rainbowness) * math.pi
        b = blending
        hue = (max(0,255*(math.cos(x/w)+b)/(1+b)),max(0,255*(math.cos((x-(r/2))/w)+b)/(1+b)),max(0,255*(math.cos((x-r)/w))+b)/(1+b))
        r = min(max(hue[0]*val*chroma+(math.pow(val,1.5)*whiteness),hue[0]*0.1),maxVal)
        g = min(max(hue[1]*val*chroma+(math.pow(val,1.5)*whiteness),hue[1]*0.1),maxVal)
        b = min(max(hue[2]*val*chroma+(math.pow(val,1.5)*whiteness),hue[2]*0.1),maxVal)
        pixels[(half+i)+buffer] = (r,g,b)
        pixels[(half-(i+1))+buffer] = (r,g,b)
        i += 1
    scroll = scroll + ((0.1+scrollJuice) * scrollSpeed)
    pixels.show()

def fire():
    global smoothing
    for i in range(pixelCount):
        if flamePixels[i][2] == 0: #Setup
            flamePixels[i][0] = random.randint(20,30) #Hue
            flamePixels[i][1] = random.randint(50,60) #Brightness
            flamePixels[i][2] = random.randint(5,20) #Flicker speed
            flamePixels[i][3] = 1 #Flicker direction
        if 0 < i < pixelCount - 1: #Smoothing
            flamePixels[i][1] -= (flamePixels[i][1]-flamePixels[i-1][1]) * smoothing
            flamePixels[i][1] -= (flamePixels[i][1]-flamePixels[i+1][1]) * smoothing
        if flamePixels[i][3] == 1: #Flicker up
            flamePixels[i][1] += flamePixels[i][2] / 1
            flamePixels[i][0] -= flamePixels[i][2] / 25
            if flamePixels[i][1] >= 255:
                flamePixels[i][1] = 255
                flamePixels[i][3] = -1
        if flamePixels[i][3] == -1: #Flicker down
            flamePixels[i][1] -= flamePixels[i][2] / 2
            flamePixels[i][0] += flamePixels[i][2] / 35
            if flamePixels[i][1] <= 20:
                flamePixels[i][1] = 20
                flamePixels[i][3] = 1
                flamePixels[i][2] = random.randint(5,20)
                flamePixels[i][0] = random.randint(20,30)
        hue = wheel(flamePixels[i][0]) #Display
        br = flamePixels[i][1] / 255
        pixels[i] = (hue[0]*br,hue[1]*br,0)
    pixels.show()

print("Running...")
while True: #Running loop
    dcWait = dcWait + 1
    if btn.value == False:
        if pressed == False:
            pressed = True
            if dcWait < 20: #Double click to change mode
                animationMode = animationMode + 1
                if animationMode > 1:
                    animationMode = 0
                print("Mode is now mode: " + str(animationMode))
                brightness = brightness + brIncrement #counteracts the increase from the first click when double clicking
                pixels.brightness = brightness
            else:
                brightness = brightness - brIncrement
                if brightness < -0.01: #floating point error solution
                    brightness = 1
                pixels.brightness = brightness
                print("Brightness is now: " + str(brightness * 100) + "%")
                dcWait = 0

    else:
        pressed = False

    if (animationMode == 0):
        if supervisor.runtime.serial_bytes_available:
            downtime = 0
            audioVis(1)
        else:
            downtime += 1
            if downtime > 100:
                audioVis(0)
    if (animationMode == 1):
        fire()






