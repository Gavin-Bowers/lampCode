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

#General Parameters
pressed = False #Button value
dcWait = 0 #Double click timer
animationMode = 0 #Which animation is displaying
brightness = 1 #LED Brightness
brIncrement = 0.2 #Amount the brightness changes per button press. 0 to 1. default 0.2

#Utilities

def wheel(x, blending): #(Turns 0-255 into color from r-g-b. b is for blending, from -0.8 to 1)
    hue = colorCalc([(255,0,0),(0,255,0),(0,0,255)], x, blending, 255)
    return (hue)

def colorCalc(colors, x, blending, r): #r is for range
    d = len(colors)
    wRed = 0.0 #sum of weighted red values
    sumRed = 0.0 #sum of red weights
    wGreen = 0.0
    sumGreen = 0.0
    wBlue = 0.0
    sumBlue = 0.0
    for i in range(d):
        weight = max(0,(math.cos((2*math.pi*(x-((i*r)/d)))/r)+blending)/(1+blending))
        wRed += colors[i][0] * weight
        sumRed += weight
        wGreen += colors[i][1] * weight
        sumGreen += weight
        wBlue += colors[i][2] * weight
        sumBlue += weight
    red = math.floor(wRed / sumRed)
    green = math.floor(wGreen / sumGreen)
    blue = math.floor(wBlue / sumBlue)
    color = (red,green,blue)
    return(color)

#Modes:
class audioVisualizer():
    def __init__(self, colors, rainbowness, blending, scrollSpeed):
        global half
        self.colors = colors
        self.scroll = 0.0 #Don't touch
        self.scrollSpeed = scrollSpeed #Scroll speed. Default is 1. Advisable to change inversely to rainbowness
        self.scrollJuice = 0.0
        self.chroma = 0.02 #Factor of the raw color value. Default is 0.01
        self.whiteness = 0.1 #Factor of the value added to each color. Default is 0.15
        self.maxVal = 255 #Max R/G/B value. Setting this above 255 allows for inverted colors by wrapping around
        self.rainbowness = rainbowness #How many colors to display at once. Works if greater than 0, but the reasonable range is from 0 to 2. 80 is fun
        self.blending = blending #How blended the colors are. Default is 0.5. Works reasonably from 0 to 1
        self.lightshow = []
        for i in range(half):
            self.lightshow.append(0)
        pixels.fill((0,0,0))

    def update(self):
        value = bytes(input(), 'utf-8')
        temp1 = value.strip(b' ')
        temp2 = temp1.split(b' ')
        self.lightshow.clear()
        for i in range(half):
            try:
                val = temp2[min(i,len(temp2)-1)]
            except ValueError:
                val = 0
            self.lightshow.append(val)

    def display(self):
        global half, buffer
        for i in range(half):
            try:
                val = min(100.0,float(self.lightshow[min(i,len(self.lightshow)-1)]))
            except ValueError:
                val = 0.0
            self.scrollJuice += min(0.0002 * math.pow(val,2),2)
            hue = colorCalc(self.colors, i - self.scroll, self.blending, 20 / self.rainbowness)
            r = min(max(hue[0]*val*self.chroma+(math.pow(val,1.5)*self.whiteness),hue[0]*0.1),self.maxVal)
            g = min(max(hue[1]*val*self.chroma+(math.pow(val,1.5)*self.whiteness),hue[1]*0.1),self.maxVal)
            b = min(max(hue[2]*val*self.chroma+(math.pow(val,1.5)*self.whiteness),hue[2]*0.1),self.maxVal)
            pixels[(half+i)+buffer] = (r,g,b)
            pixels[(half-(i+1))+buffer] = (r,g,b)
            i += 1
        self.scroll = self.scroll + ((0.1+self.scrollJuice) * self.scrollSpeed)
        self.scrollJuice = 0.0
        pixels.show()

class fire():
    def __init__(self, color):
        global pixelCount, buffer
        self.color = color
        self.smoothing = 0.01 #Flame smoothing
        self.flamePixels = []
        for i in range(pixelCount - buffer):
            self.flamePixels.append([0,0,0,0]) #hue, brightness, Flicker speed, Flicker direction

    def display(self):
        global pixelCount, buffer
        fp = self.flamePixels
        for i in range(pixelCount - buffer):
            if fp[i][2] == 0: #Setup
                fp[i][0] = random.randint(self.color - 5,self.color + 5) #Hue
                fp[i][1] = random.randint(50,60) #Brightness
                fp[i][2] = random.randint(5,20) #Flicker speed
                fp[i][3] = 1 #Flicker direction
            if 0 < i < pixelCount - 1: #Smoothing
                fp[i][1] -= (fp[i][1]-fp[max(i-1,0)][1]) * self.smoothing
                fp[i][1] -= (fp[i][1]-fp[min(i+1,pixelCount-buffer-1)][1]) * self.smoothing
            if fp[i][3] == 1: #Flicker up
                fp[i][1] += fp[i][2] / 1
                fp[i][0] -= fp[i][2] / 25
                if fp[i][1] >= 255:
                    fp[i][1] = 255
                    fp[i][3] = -1
            if fp[i][3] == -1: #Flicker down
                fp[i][1] -= fp[i][2] / 2
                fp[i][0] += fp[i][2] / 35
                if fp[i][1] <= 20:
                    fp[i][1] = 20
                    fp[i][3] = 1
                    fp[i][2] = random.randint(5,20)
                    fp[i][0] = random.randint(self.color - 5,self.color + 5)
            hue = wheel(fp[i][0],0.5) #Display
            br = fp[i][1] / 255
            pixels[i + buffer] = (hue[0]*br,hue[1]*br,0)
        pixels.show()

print("Running...") #Startup
av1 = audioVisualizer([(255,0,0),(0,255,0),(0,0,255)],1, 0.7, 3)
av2 = audioVisualizer([(10,230,10),(255,255,255),(255,10,0)],0.5, 0.1, 5)
fr1 = fire(20)

while True: #Running loop
    dcWait = dcWait + 1
    if btn.value == False:
        if pressed == False:
            pressed = True
            if dcWait < 20: #Double click to change mode
                animationMode = animationMode + 1
                if animationMode > 2:
                    animationMode = 0
                print("Mode is now mode: " + str(animationMode))
                brightness += brIncrement
                pixels.brightness = brightness
                dcWait = 20
            else:
                brightness -= brIncrement
                if brightness < -0.01 or brightness > 1: #floating point error solution
                    brightness = 1
                pixels.brightness = brightness
                print("Brightness is now: " + str(brightness * 100) + "%")
                dcWait = 0

    else:
        pressed = False

    if (animationMode == 0):
        if supervisor.runtime.serial_bytes_available:
            av1.update()
        av1.display()

    if (animationMode == 2):
        if supervisor.runtime.serial_bytes_available:
            av2.update()
        av2.display()

    if (animationMode == 1):
        fr1.display()
