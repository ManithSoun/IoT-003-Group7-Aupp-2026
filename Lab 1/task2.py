import network
import urequests
import time

# ===== WIFI =====
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# ===== TELEGRAM =====
BOT_TOKEN = "8378245115:AAEwSFBK-Noxo38CT-NS8kE4p8Ht9qMkuBA"
CHAT_ID = "-5280207636"
URL = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

# ===== WIFI CONNECT =====
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

while not wifi.isconnected():
    time.sleep(1)

print("WiFi connected")

last_update_id = 0

# ===== MAIN LOOP =====
while True:
    try:
        r = urequests.get(URL + "?offset={}".format(last_update_id + 1))
        data = r.json()
        r.close()

        for msg in data["result"]:
            last_update_id = msg["update_id"]
            text = msg["message"]["text"]
            chat_id = msg["message"]["chat"]["id"]

            if str(chat_id) == CHAT_ID:
                print("Received from Telegram:")
                print(text)
                print("----------------------")

    except Exception as e:
        print("Error:", e)

    time.sleep(2)
