import network
import urequests
import time

# WIFI CONFIG
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# TELEGRAM CONFIG
BOT_TOKEN = "bot_token"
CHAT_ID = "chat_id"  

SEND_URL = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
GET_URL  = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

# WIFI CONNECT
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

while not wifi.isconnected():
    time.sleep(1)

print("WiFi connected")

# SEND MESSAGE FUNCTION
def send_message(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    r = urequests.post(SEND_URL, json=payload)
    r.close()

# Use send_message() ONCE (Task 2 requirement)
send_message("Task 2: ESP32 connected to Telegram")

# MAIN LOOP (RECEIVE & PRINT)
last_update_id = 0

while True:
    try:
        url = GET_URL + "?offset={}".format(last_update_id + 1)
        r = urequests.get(url)
        data = r.json()
        r.close()

        for upd in data.get("result", []):
            last_update_id = upd["update_id"]

            msg = upd.get("message")
            if not msg:
                continue

            text = msg.get("text", "")
            chat_id = msg["chat"]["id"]

            if str(chat_id) == CHAT_ID:
                print("Received from Telegram:")
                print(text)
                print("----------------------")

    except Exception as e:
        print("Error:", e)

    time.sleep(2)
