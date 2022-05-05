import supervisor
import board
import neopixel #If missing, download adafruit circuitpython 6.X bundle and move neopixel.mpy into the drive for this device
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

#Pointless, but seemingly needed audio configuration

mic = audiobusio.PDMIn(clock_pin=board.GP3, data_pin=board.GP2,mono=True, sample_rate=16000, bit_depth=16)
btn = DigitalInOut(board.GP9)
btn.direction = Direction.INPUT
btn.pull = Pull.UP

#Led Setup

pixelCount = 51 #Change to the number of LEDs on your light strip
buffer = 1 #the number of pixels you don't want to use at the start of the strip (probably set this to 0)
half = math.floor((pixelCount-buffer)/2.0) #If the (pixelCount - buffer) is odd, stuff might break, but hopefully not
pixels = neopixel.NeoPixel(board.GP5, pixelCount, brightness=0.3, auto_write=False) #This actually sets the universal brightness

#General Parameters

pressed = False #Mode switching stuff
animationMode = 0

#Utilities

def wheel(pos):
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

# MODES:

#Flame Parameters

smoothing = 0.01 #Flame smoothing
flamePixels = []
for i in range(pixelCount):
    flamePixels.append([0,0,0,0]) #hue, brightness, Flicker speed, Flicker direction

def runFireAnimation(brightness):
    global smoothing
    for i in range(pixelCount):
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

        if flamePixels[i][2] == 0: #setup
            flamePixels[i][0] = random.randint(20,30) #hue
            flamePixels[i][1] = random.randint(50,60) #brightness
            flamePixels[i][2] = random.randint(5,20) #flicker speed
            flamePixels[i][3] = 1 #flicker direction

        hue = wheel(flamePixels[i][0])
        br = flamePixels[i][1] / 255
        pixels[i] = (hue[0]*br*brightness,hue[1]*br*brightness,0)
    pixels.show()

#Audio Visualizer Parameters

downtime = 0 #no touch
scroll = 0.0 #no touch
chroma = 0.01 #Factor of the raw color value
whiteness = 0.1 #Factor of the value added to each color ((val ^ 1.5) * this)
maxVal = 255 #Max R/G/B value. Setting this above 255 allows for inverted colors by wrapping around
rainbowness = 3 #How many colors display at once. Causes issues if set higher than 10

def audioVis(hasData):
    global half, buffer, scroll, chroma, rainbowness, contrast, whiteness
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
        scrollJuice += min(0.0005 * val * val,5)
        temp = scroll+((half-i)*rainbowness)
        if temp < 0:
            temp = 255 + temp #Rainbow wrapping logic
        if temp > 255:
            temp = 255 - temp
        hue = wheel(temp)
        r = min(max(hue[0]*val*chroma+(math.sqrt(val*val*val)*whiteness),hue[0]*0.1),maxVal)
        g = min(max(hue[1]*val*chroma+(math.sqrt(val*val*val)*whiteness),hue[1]*0.1),maxVal)
        b = min(max(hue[2]*val*chroma+(math.sqrt(val*val*val)*whiteness),hue[2]*0.1),maxVal)
        pixels[(half+i)+buffer] = (r,g,b)
        pixels[(half-(i+1))+buffer] = (r,g,b)
        i += 1
    scroll = scroll + 1 + scrollJuice
    if scroll+(half*rainbowness) > 255:
        scroll = -(half*rainbowness) #Because this value is added to the "front" of the rainbow, it cancels out so it loops properly
    pixels.show()

print("Running...")

while True:
    if btn.value == False: #Mode switching
        if pressed == False:
            pressed = True
            animationMode = animationMode + 1
            if animationMode > 4:
                animationMode = 0
            print("Mode is now mode: ", animationMode)
    else:
        pressed = False

    if (animationMode == 0):
        if supervisor.runtime.serial_bytes_available:
            downtime = 0
            audioVis(1)
        else:
            downtime += 1
            if downtime > 999:
                audioVis(0)

    if (animationMode == 1):
        runFireAnimation(1)

    if (animationMode == 2):
        runFireAnimation(0.7)

    if (animationMode == 3):
        runFireAnimation(0.4)

    if (animationMode == 4):
        pixels.fill((0,0,0))
        pixels.show()
        time.sleep(0.1)





