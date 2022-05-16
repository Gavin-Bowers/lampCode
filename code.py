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

pressed = False #Button value
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

def colorCalc(colors, x, blending, r): #r is for range
    d = len(colors)
    weightedColors = []
    for i in range(d):
        weight = max(0,(math.cos((2*math.pi*(x-((i*r)/d)))/r)+blending)/(1+blending))
        weightedColors.append((colors[i][0],colors[i][1],colors[i][2],weight))
    return(colorWeightedAverage(weightedColors))

def colorWeightedAverage(weightedColors): #(red,green,blue,weight)
    wrs = 0.0 #weighted red sum
    wgs = 0.0 #weighted green sum
    wbs = 0.0 #weighted blue sum
    sw = 0.001 #sum of weights
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
    def __init__(self, colors, accentColor, accentWeight, rainbowness, scrollSettings, blending, chroma, maxVal, minimum, colorDesc):
        global HALF, BUFFER, modes
        modes[0].insert(0,self)
        self.scroll = 0.0
        self.scrollJuice = 0.0
        self.scrollSpeed = scrollSettings[0]
        self.scrollResponsiveness = scrollSettings[1]
        self.scrollNonlinearity = scrollSettings[2]
        self.scrollMaximum = scrollSettings[3]
        self.scrollBaseline = scrollSettings[4]
        self.maxVal = maxVal
        self.colors = colors
        self.accentColor = accentColor
        self.accentWeight = accentWeight
        self.minimum = minimum
        self.rainbowness = rainbowness
        self.blending = blending
        self.chroma = chroma
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
                value = min(100.0,float(self.lightshow[min(i,len(self.lightshow)-1)])) #0 - 100
            except ValueError:
                value = 0.0
            self.scrollJuice += 0.0001 * self.scrollResponsiveness * math.pow(value,self.scrollNonlinearity)
            hue = colorCalc(self.colors, i - self.scroll, self.blending, 20 / self.rainbowness)
            hue2 = colorWeightedAverage([(hue[0],hue[1],hue[2],50),
            (self.accentColor[0],self.accentColor[1],self.accentColor[2],value * self.accentWeight)])
            r = min(max(hue2[0]*value*self.chroma,hue2[0]*self.minimum),self.maxVal)
            g = min(max(hue2[1]*value*self.chroma,hue2[1]*self.minimum),self.maxVal)
            b = min(max(hue2[2]*value*self.chroma,hue2[2]*self.minimum),self.maxVal)
            pixels[(HALF+i)+BUFFER] = (r,g,b)
            pixels[(HALF-(i+1))+BUFFER] = (r,g,b)
            i += 1
        self.scroll += ((self.scrollBaseline+min(self.scrollJuice,self.scrollMaximum)) * self.scrollSpeed)
        self.scrollJuice = 0.0
        pixels.show()

class fire():
    def __init__(self, color, accentColor, accent2, colorDesc):
        global N_PIXELS, BUFFER, modes
        modes[1].insert(0,self)
        self.color = color
        self.accentColor = accentColor
        self.accent2 = accent2
        self.smoothing = 0.008 #Flame smoothing
        self.colorDesc = colorDesc
        self.desc = "Fire animation"
        self.flamePixels = []
        for i in range(N_PIXELS - BUFFER):
            self.flamePixels.append([0,0,0,0]) #Progress (0-100), Flicker speed, Flicker direction

    def run(self):
        self.display()

    def display(self):
        fp = self.flamePixels
        for i in range(N_PIXELS - BUFFER):
            if fp[i][2] == 0: #Setup
                fp[i][0] = 0 #Progress
                fp[i][1] = random.randint(5,15) #Flicker speed
                fp[i][2] = 1 #Flicker direction
            if 0 < i < N_PIXELS - 1: #Smoothing
                fp[i][0] -= (fp[i][0]-fp[max(i-1,0)][0]) * self.smoothing
                fp[i][0] -= (fp[i][0]-fp[min(i+1,N_PIXELS-BUFFER-1)][0]) * self.smoothing
            if fp[i][2] == 1: #Flicker up
                fp[i][0] += fp[i][1]
                if fp[i][0] >= 100:
                    fp[i][0] = 100
                    fp[i][2] = -1
            if fp[i][2] == -1: #Flicker down
                fp[i][0] -= fp[i][1] /2
                if fp[i][0] <= 0:
                    fp[i][0] = 0
                    fp[i][1] = random.randint(5,15)
                    fp[i][2] = 1
            hue = colorWeightedAverage([(self.color[0],self.color[1],self.color[2],100-fp[i][0]),
            (self.accent2[0],self.accent2[1],self.accent2[2],max(0,(fp[i][0] - 80)*2)),
            (self.accentColor[0],self.accentColor[1],self.accentColor[2],fp[i][0])])
            pixels[i + BUFFER] = (math.floor(hue[0]),math.floor(hue[1]),math.floor(hue[2]))
        pixels.show()

def main():
    global btn, modes, pressed
    WHITE = (255,255,255)
    BLACK = (0,0,0)
    RED = (255,0,0)
    ORANGE = (255, 150, 0)
    YELLOW = (255,250,0)
    LIME = (200,255,0)
    GREEN = (0,255,0)
    TEAL = (0,250,200)
    BLUE = (0,0,255)
    PURPLE = (150,0,255)

    #Color schemes:
    #Order of color schemes is reversed from the order they are established in

    #Audio Visualizer Parameters:
    #Colors is an ordered list of the colors in the format: [(r,g,b),(r,g,b)...] Color constants also work.
    #Accent color is the color the frequency volumes display as.
    #Rainbowness is how densly packed the colors are.
    #Scroll settings is a tuple of the following settings:
        #Scroll speed is applied multiplicatively after everything else. It's advisable to change it inversely to rainbowness.
        #Audio responsiveness is how much scroll responds to audio.
        #Audio nonlinearity is the power the audio effect is raised to.
        #Maximum is the limit of how much the audio can increase the scroll speed
        #Scroll baseline is how fast it scrolls at minimum.
    #Blending is how much the colors overlap. Higher values yield more in-between colors and high values cause pastel colors.
        #Blending should typically be lower with higher numbers of colors.
    #Chroma is the factor that the frequency volume increases the colored brightness. Setting to negative causes wacky wrapping around.
    #MaxVal is the maximum output r/g/b value. Increasing above 255 allows for inverted colors by wrapping around.
    #Minimum sets the dimmest that the colors can display.
    #ColorDesc is a description of the color scheme.

    #Parameters: (colors,           accentColor, accentWeight, rainbowness, scrollSettings, blending, chroma,      maxVal,    minimum,   colorDesc )
    #Defaults:   ([RED,GREEN,BLUE], WHITE,       1             1,                           0.5,      0.02,        255,       0.05       "Default" )
    #Ranges:     (0-255             0-255        0-2           Not 0           (below)      >=-0.8    Any real     >0         >0         Any string)
    #Reasonable: (0-255             0-255        0.5 - 1.5     0.01 - 2                     -0.8 - 1  0.01 - 0.05  255 - 300  0.01 - 0.1 Any string)

    #Scroll settings: (speed,  responsiveness, nonlinearity, maximum, baseline)
    #Default:         (2       2               2             5        0.2     )

    av = audioVisualizer(
    [(120,0,0)], #colors
    (-240,0,0), #accent
    1, #accentWeight
    1, #rainbowness
    (0,2,2,3,0.2), #speed, responsiveness, nonlinearity, maximum, baseline
    2, #blending
    0.00, #chroma
    255, #maxVal
    0.1, #minimum
    "Inverse red") #description

    av = audioVisualizer(
    [GREEN,WHITE,RED], #colors
    WHITE, #accent
    1, #accentWeight
    0.5, #rainbowness
    (1,1,2,5,0.2), #speed, responsiveness, nonlinearity, maximum, baseline
    0.1, #blending
    0.02, #chroma
    255, #maxVal
    0.05, #minimum
    "Mexico") #description

    av = audioVisualizer(
    [BLUE, TEAL], #colors
    YELLOW, #accent
    2, #accentWeight
    0.5, #rainbowness
    (1,2,2,3,0.2), #speed, responsiveness, nonlinearity, maximum, baseline
    1, #blending
    0.01, #chroma
    255, #maxVal
    0.05, #minimum
    "Sea") #description

    av = audioVisualizer(
    [RED,GREEN,BLUE], #colors
    WHITE, #accent
    0.6, #accentWeight
    0.5, #rainbowness
    (1.5,1,2,3,0.2), #speed, responsiveness, nonlinearity, maximum, baseline
    0.4, #blending
    0.02, #chroma
    255, #maxVal
    0.1, #minimum
    "Rainbow") #description

    #Fire color schemes

    fr = fire(
    (150,0,0), #Color
    GREEN, #Secondary color
    WHITE, #Tip color
    "Cursed Mexico Fire") #Description

    fr = fire(
    (0,0,0), #Color
    (255,255,255), #Secondary color
    (255,255,255), #Tip color
    "Purity") #Description

    fr = fire(
    (0,5,30), #Color
    (0,80,50), #Secondary color
    (5,120,60), #Tip color
    "Blue fire") #Description

    fr = fire(
    (0,0,4), #Color
    (150,70,0), #Secondary color
    (350,20,0), #Tip color
    "Gas stove fire") #Description

    fr = fire(
    (30,15,0), #Color
    (60,10,0), #Secondary color
    (120,30,0), #Tip color
    "Orange Red") #Description

    ########################################

    btn.direction = Direction.INPUT
    btn.pull = Pull.UP
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
