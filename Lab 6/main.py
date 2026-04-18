from machine import Pin, SPI
from mfrc522 import MFRC522
import network
import urequests
import time
import os
import sdcard

SSID = "your-wifi"
PASSWORD = "your-password"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)
print("Connecting WiFi", end="")
while not wifi.isconnected():
    print(".", end="")
    time.sleep(0.5)
print("\nConnected:", wifi.ifconfig())

# Firestore
PROJECT_ID = "group7-iot"
BASE_URL = "https://firestore.googleapis.com/v1/projects/{}/databases/(default)/documents".format(PROJECT_ID)

spi = SPI(1, baudrate=1000000,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = MFRC522(spi=spi, gpioRst=Pin(22), gpioCs=Pin(16))

buzzer = Pin(4, Pin.OUT)
buzzer.value(0)

# send to SD card
CSV_FILE = "/sd/attendance.csv"
sd_ok = False

try:
    spi2 = SPI(2, baudrate=100000, polarity=0, phase=0,
               sck=Pin(14), mosi=Pin(15), miso=Pin(2))
    sd = sdcard.SDCard(spi2, Pin(13))
    os.mount(sd, "/sd")
    print("SD card mounted:", os.listdir("/sd"))
    sd_ok = True

    try:
        os.stat(CSV_FILE)
    except OSError:
        with open(CSV_FILE, "w") as f:
            f.write("UID,Name,StudentID,Major,DateTime\n")

except Exception as e:
    print("SD card failed:", e)
    print("Continuing without SD card...")


def get_datetime():
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5])

def beep(duration):
    buzzer.value(1)
    time.sleep(duration)
    buzzer.value(0)

def fetch_students():
    students = {}
    try:
        print("Fetching students from Firestore...")
        res = urequests.get(BASE_URL + "/students")
        data = res.json()
        res.close()
        for doc in data.get("documents", []):
            fields = doc.get("fields", {})
            uid        = fields.get("uid",        {}).get("stringValue", "")
            name       = fields.get("name",       {}).get("stringValue", "")
            student_id = fields.get("student_id", {}).get("stringValue", "")
            major      = fields.get("major",      {}).get("stringValue", "")
            if uid:
                students[uid] = {"name": name, "student_id": student_id, "major": major}
        print("Loaded {} student(s)".format(len(students)))
    except Exception as e:
        print("Failed to fetch students:", e)
    return students

def save_to_sd(uid, name, student_id, major, dt):
    try:
        with open(CSV_FILE, "a") as f:
            f.write("{},{},{},{},{}\n".format(uid, name, student_id, major, dt))
        print("Saved to SD")
    except Exception as e:
        print("SD write error:", e)

def send_to_firestore(uid, name, student_id, major, dt):
    data = {
        "fields": {
            "uid":        {"stringValue": uid},
            "name":       {"stringValue": name},
            "student_id": {"stringValue": student_id},
            "major":      {"stringValue": major},
            "datetime":   {"stringValue": dt}
        }
    }
    try:
        res = urequests.post(BASE_URL + "/attendance", json=data)
        print("Sent:", res.text)
        res.close()
    except Exception as e:
        print("Error sending:", e)


STUDENTS = fetch_students()

# main
print("Scan RFID...")

while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()
        if stat == rdr.OK:
            uid_str = "".join([str(i) for i in uid])
            print("UID:", uid_str)

            if uid_str in STUDENTS:
                student = STUDENTS[uid_str]
                dt = get_datetime()
                print("Welcome,", student["name"])
                beep(0.3)
                if sd_ok:
                    save_to_sd(uid_str, student["name"], student["student_id"], student["major"], dt)
                send_to_firestore(uid_str, student["name"], student["student_id"], student["major"], dt)

            else:
                print("Unknown Card")
                beep(3)

            time.sleep(2)
