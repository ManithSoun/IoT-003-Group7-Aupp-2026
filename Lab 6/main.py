from machine import Pin, SPI
from mfrc522 import MFRC522
import network
import urequests
import time

# Wi-Fi
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
PROJECT_ID = "your-firestore-id"
BASE_URL = "https://firestore.googleapis.com/v1/projects/{}/databases/(default)/documents".format(PROJECT_ID)

# RFID
spi = SPI(1, baudrate=1000000,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = MFRC522(spi=spi, gpioRst=Pin(22), gpioCs=Pin(16))

# Buzzer
buzzer = Pin(4, Pin.OUT)
buzzer.value(0)

# Helpers
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

# ── Boot: load students ────────────────────────────────────────────────────
STUDENTS = fetch_students()

# ── Main loop ──────────────────────────────────────────────────────────────
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
                send_to_firestore(uid_str, student["name"], student["student_id"], student["major"], dt)

            else:
                print("Unknown Card")
                beep(3)

            time.sleep(2)
