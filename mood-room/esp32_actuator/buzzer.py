from machine import Pin, PWM
import time

BUZZER_PIN = 4
buzzer = PWM(Pin(BUZZER_PIN), freq=440, duty=0)

def off():
    buzzer.duty(0)

def beep(freq=440, duration=0.05, times=1, gap=0.05):
    for _ in range(times):
        buzzer.freq(freq)
        buzzer.duty(512)
        time.sleep(duration)
        buzzer.duty(0)
        time.sleep(gap)

def happy_tone():
    beep(880, 0.05, 2, 0.05)

def sad_tone():
    beep(300, 0.2, 1)

def angry_tone():
    beep(1000, 0.05, 3, 0.05)

def fear_tone():
    beep(600, 0.05, 3, 0.05)

def surprise_tone():
    beep(880, 0.05, 2, 0.1)

def neutral_tone():
    off()
