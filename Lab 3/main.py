import network
import time
from machine import Pin, PWM
import urequests as requests
import tm1637

#CONFIG 
WIFI_SSID = "Roasters home"
WIFI_PASS = "matcha520"

BLYNK_TOKEN = "G_QqSFfuob7ebUJ1RrcvrABHM7g-iNkF"
BLYNK_API  = "http://blynk.cloud/external/api"

IR_PIN = 12
SERVO_PIN = 13
CLK_PIN = 17
DIO_PIN = 16

V_IR = "V0"
V_SERVO = "V2"
V_COUNTER = "V3"
V_MODE = "V4"   # NEW SWITCH

#WIF
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(WIFI_SSID, WIFI_PASS)

while not wifi.isconnected():
    time.sleep(1)

print("WiFi connected")

#HARDWARE
ir = Pin(IR_PIN, Pin.IN, Pin.PULL_UP)
servo = PWM(Pin(SERVO_PIN), freq=50)

display = tm1637.TM1637(CLK_PIN, DIO_PIN)
display.set_brightness(3)
display.show_number(0)

#SERVO
def angle_to_duty(angle):
    min_duty = 40
    max_duty = 115
    return int(min_duty + (angle / 180) * (max_duty - min_duty))

servo.duty(angle_to_duty(0))

#BLYNK
def blynk_update(pin, value):
    try:
        value = str(value).replace(" ", "%20")
        url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&{pin}={value}"
        r = requests.get(url)
        r.close()
    except:
        pass

def blynk_get(pin):
    try:
        url = f"{BLYNK_API}/get?token={BLYNK_TOKEN}&{pin}"
        r = requests.get(url)
        data = r.text
        r.close()
        if data == "[]":
            return None
        return int(data.strip('[]"'))
    except:
        return None

# ---------- VARIABLES ----------
count = 0
last_ir = "Not Detected"
last_angle = None

# Initial display + Blynk sync
display.show_number(0)
blynk_update(V_COUNTER, 0)
blynk_update(V_IR, "Not Detected")

servo.duty(angle_to_duty(0))  # Gate closed

print("System Running")

# ---------- MAIN LOOP ----------
while True:

    # READ MODE SWITCH
    mode = blynk_get(V_MODE)
    if mode is None:
        mode = 1  # default AUTO

    # AUTO MODE
    if mode == 1:

        raw = ir.value()
        detected = 1 if raw == 0 else 0

        if detected != last_ir:

            if detected == 1:
                # Open gate
                servo.duty(angle_to_duty(90))

                count += 1
                display.show_digit(count)
                blynk_update(V_COUNTER, count)

                blynk_update(V_IR, "Detected")
                print("AUTO - Detected")

            else:
                servo.duty(angle_to_duty(0))
                blynk_update(V_IR, "Not Detected")
                print("AUTO - Not Detected")

            last_ir = detected

    # MANUAL MODE
    else:
        # IR ignored

        angle = blynk_get(V_SERVO)
        if angle is not None and angle != last_angle:
            servo.duty(angle_to_duty(angle))
            last_angle = angle
            print("MANUAL - Servo angle:", angle)

    time.sleep(0.2)