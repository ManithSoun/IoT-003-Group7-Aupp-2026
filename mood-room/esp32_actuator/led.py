from machine import Pin
import neopixel
import time

NUM_LEDS = 24
NEO_PIN  = 23
np = neopixel.NeoPixel(Pin(NEO_PIN), NUM_LEDS)

def off():
    for i in range(NUM_LEDS):
        np[i] = (0, 0, 0)
    np.write()

def solid(r, g, b):
    for i in range(NUM_LEDS):
        np[i] = (r, g, b)
    np.write()

def flash(r, g, b, times=3):
    for _ in range(times):
        solid(r, g, b)
        time.sleep(0.15)
        off()
        time.sleep(0.15)
    solid(r, g, b)

def pulse(r, g, b, steps=5):
    for i in range(steps):
        factor = i / steps
        solid(int(r*factor), int(g*factor), int(b*factor))
        time.sleep(0.02)
    for i in range(steps, 0, -1):
        factor = i / steps
        solid(int(r*factor), int(g*factor), int(b*factor))
        time.sleep(0.02)

def spin(r, g, b, rounds=1):
    for _ in range(rounds):
        for i in range(NUM_LEDS):
            off()
            np[i] = (r, g, b)
            np.write()
            time.sleep(0.03)
