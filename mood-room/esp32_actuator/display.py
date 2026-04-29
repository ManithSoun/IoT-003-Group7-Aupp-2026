from machine import Pin, SoftI2C
import ssd1306

SDA_PIN = 21
SCL_PIN = 22

i2c = SoftI2C(scl=Pin(SCL_PIN), sda=Pin(SDA_PIN))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

EMOTION_INFO = {
    "happy":    (":) HAPPY",    "Upbeat playlist"),
    "sad":      (":( SAD",      "Lo-fi playlist"),
    "angry":    (">:( ANGRY",   "Calm playlist"),
    "fear":     ("! FEAR",      "Soothing playlist"),
    "surprise": (":O SURPRISE", "Upbeat playlist"),
    "neutral":  (":| NEUTRAL",  "Chill playlist"),
    "off":      ("OFFLINE",     ""),
}

def show(emotion):
    emoji, music = EMOTION_INFO.get(emotion, (emotion.upper(), ""))
    display.fill(0)
    display.text("MoodRoom", 25, 0)
    display.text("--------", 20, 10)
    display.text(emoji, 0, 25)
    display.text("Now playing:", 0, 42)
    display.text(music, 0, 54)
    display.show()

def startup():
    display.fill(0)
    display.text("MoodRoom", 25, 20)
    display.text("Starting...", 15, 40)
    display.show()

def wifi_ok(ip):
    display.fill(0)
    display.text("WiFi OK!", 25, 10)
    display.text("IP:", 0, 30)
    display.text(ip, 0, 45)
    display.show()

def wifi_fail():
    display.fill(0)
    display.text("WiFi Failed!", 5, 25)
    display.show()

def off():
    display.fill(0)
    display.show()