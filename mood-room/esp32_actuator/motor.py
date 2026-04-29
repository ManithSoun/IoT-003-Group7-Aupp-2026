from machine import Pin, PWM

IN1_PIN = 26
IN2_PIN = 27
ENA_PIN = 14

in1 = Pin(IN1_PIN, Pin.OUT)
in2 = Pin(IN2_PIN, Pin.OUT)
ena = PWM(Pin(ENA_PIN), freq=2000)

def off():
    in1.value(0)
    in2.value(0)
    ena.duty(0)

def spin(speed=512):
    in1.value(1)
    in2.value(0)
    ena.duty(speed)

def slow():
    spin(300)

def medium():
    spin(512)

def fast():
    spin(1023)
