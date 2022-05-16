import supervisor
import board
import neopixel #If missing, copy from the lightshow folder onto this device
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

smallLamp = False #Change this to True for easy small lamp setup
modes = [[None for i in range(2)] for i in range(2)] #Buffer of 2 needed for some reason

if smallLamp:
    N_PIXELS = 34 #Number of LEDs
    BUFFER = 0 #The number of pixels you don't want to use at the start of the LED strip
    HALF = math.floor((N_PIXELS-BUFFER)/2.0) #If the (N_PIXELS - BUFFER) is odd, stuff might break
    pixels = neopixel.NeoPixel(board.GP0, N_PIXELS, brightness=1, auto_write=False)
    btn = DigitalInOut(board.GP2)

else:
    N_PIXELS = 51 #Number of LEDs
    BUFFER = 1 #The number of pixels you don't want to use at the start of the LED strip
    HALF = math.floor((N_PIXELS-BUFFER)/2.0) #If the (N_PIXELS - BUFFER) is odd, stuff might break
    pixels = neopixel.NeoPixel(board.GP5, N_PIXELS, brightness=1, auto_write=False) #GP0 for smaller lamps
    mic = audiobusio.PDMIn(clock_pin=board.GP3, data_pin=board.GP2,mono=True, sample_rate=16000, bit_depth=16) #My device bugs out without this
    btn = DigitalInOut(board.GP9)

#Utilities

def wheel(x, blending): #(Turns 0-255 into color from r-g-b. b is for blending, from -0.8 to 1)
    hue = colorCalc([(255,0,0),(0,255,0),(0,0,255)], x, blending, 255)
    return (hue)

def colorCalc(colors, x, blending, r): #r is for range
    d = len(colors)
    weightedColors = []
    for i in range(d):
        weight = max(0,(math.cos((2*math.pi*(x-((i*r)/d)))/r)+blending)/(1+blending))
        weightedColors.append((colors[i][0],colors[i][1],colors[i][2],weight))
    return(colorWeightedAverage(weightedColors))

def colorWeightedAverage(weightedColors): #[red,green,blue,weight]
    wrs = 0.0 #weighted red sum
    wgs = 0.0 #weighted green sum
    wbs = 0.0 #weighted blue sum
    sw = 0.0 #sum of weights
    for wc in weightedColors:
        wrs += wc[0]*wc[3]
        wgs += wc[1]*wc[3]
        wbs += wc[2]*wc[3]
        sw += wc[3]
    return((wrs/sw,wgs/sw,wbs/sw))

def isPressed(): #Returns true once when the button is pressed. Somehow works despite pressed not being global?
    global pressed, btn
    if btn.value == False:
        if pressed == False:
            pressed = True
            return True
    else:
        pressed = False
        return False

#Modes:

class audioVisualizer():
    def __init__(self, colors, rainbowness, blending, scrollSpeed, colorDesc):
        global HALF, BUFFER, modes
        modes[0].insert(0,self)
        self.colors = colors
        self.scroll = 0.0 #Don't touch
        self.scrollSpeed = scrollSpeed #Scroll speed. Default is 1. Advisable to change inversely to rainbowness
        self.scrollJuice = 0.0
        self.chroma = 0.02 #Factor of the raw color value. Default is 0.01
        self.whiteness = 0.1 #Factor of the value added to each color. Default is 0.15
        self.maxVal = 255 #Max R/G/B value. Setting this above 255 allows for inverted colors by wrapping around
        self.rainbowness = rainbowness #How many colors to display at once. Works if greater than 0, but the reasonable range is from 0 to 2. 80 is fun
        self.blending = blending #How blended the colors are. Default is 0.5. Works reasonably from 0 to 1
        self.desc = "Music visualizer and/or scrolling lightshow"
        self.colorDesc = colorDesc
        self.lightshow = []
        for i in range(HALF):
            self.lightshow.append(0)
        pixels.fill((0,0,0))

    def run(self):
        if supervisor.runtime.serial_bytes_available:
            self.update()
        self.display()

    def update(self):
        value = bytes(input(), 'utf-8')
        temp1 = value.strip(b' ')
        temp2 = temp1.split(b' ')
        self.lightshow.clear()
        for i in range(HALF):
            try:
                val = temp2[min(i,len(temp2)-1)]
            except ValueError:
                val = 0
            self.lightshow.append(val)

    def display(self):
        for i in range(HALF):
            try:
                val = min(100.0,float(self.lightshow[min(i,len(self.lightshow)-1)]))
            except ValueError:
                val = 0.0
            self.scrollJuice += min(0.0002 * math.pow(val,2),2)
            hue = colorCalc(self.colors, i - self.scroll, self.blending, 20 / self.rainbowness)
            r = min(max(hue[0]*val*self.chroma+(math.pow(val,1.5)*self.whiteness),hue[0]*0.1),self.maxVal)
            g = min(max(hue[1]*val*self.chroma+(math.pow(val,1.5)*self.whiteness),hue[1]*0.1),self.maxVal)
            b = min(max(hue[2]*val*self.chroma+(math.pow(val,1.5)*self.whiteness),hue[2]*0.1),self.maxVal)
            pixels[(HALF+i)+BUFFER] = (r,g,b)
            pixels[(HALF-(i+1))+BUFFER] = (r,g,b)
            i += 1
        self.scroll = self.scroll + ((0.1+self.scrollJuice) * self.scrollSpeed)
        self.scrollJuice = 0.0
        pixels.show()

class fire():
    def __init__(self, color, colorDesc):
        global N_PIXELS, BUFFER, modes
        modes[1].insert(0,self)
        self.color = color
        self.smoothing = 0.01 #Flame smoothing
        self.colorDesc = colorDesc
        self.desc = "Fire animation"
        self.flamePixels = []
        for i in range(N_PIXELS - BUFFER):
            self.flamePixels.append([0,0,0,0]) #hue, brightness, Flicker speed, Flicker direction

    def run(self):
        self.display()

    def display(self):
        fp = self.flamePixels
        for i in range(N_PIXELS - BUFFER):
            if fp[i][2] == 0: #Setup
                fp[i][0] = random.randint(self.color - 5,self.color + 5) #Hue
                fp[i][1] = random.randint(50,60) #Brightness
                fp[i][2] = random.randint(5,20) #Flicker speed
                fp[i][3] = 1 #Flicker direction
            if 0 < i < N_PIXELS - 1: #Smoothing
                fp[i][1] -= (fp[i][1]-fp[max(i-1,0)][1]) * self.smoothing
                fp[i][1] -= (fp[i][1]-fp[min(i+1,N_PIXELS-BUFFER-1)][1]) * self.smoothing
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
            pixels[i + BUFFER] = (hue[0]*br,hue[1]*br,0)
        pixels.show()

def main():
    global btn, modes

    #Order is reversed from the order they are established in
    av1 = audioVisualizer([(255,0,0),(0,255,0),(0,0,255)],1, 0.7, 2, "Rainbow") #colors, rainbowness, blending, scrollSpeed, color description
    av2 = audioVisualizer([(10,230,10),(255,255,255),(255,10,0)],0.5, 0.1, 5, "Mexico")
    fr1 = fire(20, "Orange Red") #Hue, color description

    btn.direction = Direction.INPUT
    btn.pull = Pull.UP
    pressed = False #Button value
    longPressTest = False
    longPressTimer = 0
    dcTest = False #Prevents single clicking while double clicking
    dcWait = 0 #Double click timer

    animationMode = 0
    colorMode = 0

    brightness = 1 #LED brightness
    BR_INC = 0.2 #Amount the brightness changes per button press. Works from 0 to 1. Default is 0.2

    while True:#Running loop

        if not btn.value and longPressTest:
            longPressTimer += 1

        if dcTest:
            dcWait += 1

        if isPressed(): #Fires on button press
            if not longPressTest:
                longPressTest = True
                longPressTimer = 0
            if not dcTest:
                dcTest = True
                dcWait = 0
            else:
                if dcWait <= 10: #Double press condition
                    if animationMode == len(modes) - 1: #List buffer isn't counted by len
                        animationMode = 0
                    else:
                        animationMode += 1
                    colorMode = 0
                    print("Mode is: " + modes[animationMode][0].desc)
                    print("Color is: " + modes[animationMode][colorMode].colorDesc)
                    dcTest = False
                    longPressTest = False

        if btn.value and longPressTest and longPressTimer >= 5: #Long press condition
            if colorMode == len(modes[animationMode]) - 3: #List buffer is counted by len for some reason
                colorMode = 0
            else:
                colorMode += 1
            print("Color is: " + modes[animationMode][colorMode].colorDesc)
            longPressTimer = 0
            longPressTest = False
            dcTest = False

        if btn.value and dcTest and dcWait > 10: #Short press condition
            brightness -= BR_INC
            if brightness < -0.01 or brightness > 1: #Deals with floating point errors
                brightness = 1
            pixels.brightness = brightness
            if brightness > 0.001: #Also deals with floating point errors
                print("Brightness is: " + str(brightness * 100) + "%")
            else:
                print("Brightness is: 0%")
            longPressTimer = 0
            longPressTest = False
            dcTest = False

        modes[animationMode][colorMode].run()

main()
