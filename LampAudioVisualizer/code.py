import supervisor
import board
import neopixel
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
from adafruit_led_animation.animation.colorcycle import ColorCycle

#Necessary but pointless audio configuration
mic = audiobusio.PDMIn(clock_pin=board.GP3, data_pin=board.GP2,mono=True, sample_rate=16000, bit_depth=16)
btn = DigitalInOut(board.GP9)
btn.direction = Direction.INPUT
btn.pull = Pull.UP

pixelCount = 51 #LED strip setup
pixels = neopixel.NeoPixel(board.GP5, pixelCount, brightness=.3, auto_write=False)

#Parameters

pressed = False #Mode switching stuff
animationMode = 0

pi = math.pi
scroll = 0.0 #Audio Visualizer parameters
curve = 200.0
chroma = 10.0
overdrive = 2 #Default is 1. Increase it to crank the brightness up. Can be decreased as well. Works from 0 to arbitrarily high, but a reasonable range is 0.5 to 4.
                #At high settings, especially bright LEDs become rainbow, which I think is because RGB values exceeding 256 wrap around

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

smoothing = 0.01

def runFireAnimation():
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
        pixels[i] = (hue[0]*br,hue[1]*br,0)
    pixels.show()

flamePixels = []
for i in range(pixelCount):
    flamePixels.append([0,0,0,0]) #hue, brightness, Flicker speed, Flicker direction

def runAudioVisualizer():
    global scroll, curve, chroma, overdrive, pi
    if supervisor.runtime.serial_bytes_available: #Take serial input for lightshow
        value = bytes(input(), 'utf-8')
        temp = value.strip(b' ')
        lightshow = temp.split(b' ')
        pixels.fill((0,0,0))
        i = 0
        val = 0.0
        for light in lightshow:
            if i < 26:
                j=abs(25-i)
                try:
                    val = min(100.0,float(light))
                except ValueError:
                    val = 0
                scroll -= min(0.0004 * val * val,1) + 0.005 #Sets the rainbow scroll speed, which is based on total volume squared. It has a min and max value, but the min value doesn't work sometimes
                hue1 = math.cos((j-(00*pi)+scroll)/(3*pi)) #Finds the Red value for the LED with sinusoids so the rainbow can scroll
                r = overdrive*max(0,val*((250-(hue1))/curve)+(hue1*chroma)) #Makes the LED whiter as volume at that frequency increases
                hue2 = math.cos((j-(25*pi)+scroll)/(3*pi)) #Green value
                g = overdrive*max(0,val*((250-(hue2))/curve)+(hue2*chroma))
                hue3 = math.cos((j-(50*pi)+scroll)/(3*pi)) #Blue value
                b = overdrive*max(0,val*((250-(hue3))/curve)+(hue3*chroma))
                if val<2: #Improves gradient appearance when at low brightness
                    r *= (2 / max(overdrive,1)) #Allows overdrive values below 1
                    g *= (2 / max(overdrive,1))
                    b *= (2 / max(overdrive,1))
                pixels[min(25+i,51)] = (math.ceil(r),math.ceil(g),math.ceil(b))
                pixels[max(25-i,1)] = (math.ceil(r),math.ceil(g),math.ceil(b))
                i += 1
        pixels.show()

print("Running...")

while True:
    if btn.value == False: #Mode switching
        if pressed == False:
            pressed = True
            animationMode = animationMode + 1
            if animationMode > 2:
                animationMode = 0
            print("Mode is now mode: ", animationMode)
    else:
        pressed = False

    if (animationMode == 0):
        runAudioVisualizer()
    elif supervisor.runtime.serial_bytes_available: #This keeps the serial clear if the PC program is running while the lamp is on another mode
        trash = input()

    if (animationMode == 1):
        runFireAnimation()

    if (animationMode == 2):
        pixels.fill((0,0,0))
        pixels.show()
        time.sleep(0.1)





