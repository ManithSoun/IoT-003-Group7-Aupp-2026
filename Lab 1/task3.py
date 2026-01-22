import network
import urequests
import time
from machine import Pin
import dht

# WIFI CONFIG
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# TELEGRAM CONFIG
BOT_TOKEN = "8378245115:AAEwSFBK-Noxo38CT-NS8kE4p8Ht9qMkuBA"
CHAT_ID = "-5280207636"

SEND_URL = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
GET_URL  = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

# HARDWARE SETUP
sensor = dht.DHT22(Pin(4))   # DHT22 on D4
relay = Pin(2, Pin.OUT)      # Relay on D2
relay.off()

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

# MAIN LOOP
last_update_id = 0

while True:
    try:
        r = urequests.get(GET_URL + "?offset={}".format(last_update_id + 1))
        data = r.json()
        r.close()

        updates = data.get("result", [])
        if not updates:
            time.sleep(0.3)
            continue

        for upd in updates:
            last_update_id = upd["update_id"]

            msg = upd.get("message")
            if not msg:
                continue

            text = msg.get("text", "")
            chat_id = msg["chat"]["id"]

            if str(chat_id) == CHAT_ID:
                print("Command received:", text)

                # -------- /on --------
                if text == "/on":
                    relay.on()
                    print("Relay turned ON")
                    send_message("✅ Relay turned ON")

                # -------- /off --------
                elif text == "/off":
                    relay.off()
                    print("Relay turned OFF")
                    send_message("❌ Relay turned OFF")

                # -------- /status --------
                elif text == "/status":
                    sensor.measure()
                    temp = sensor.temperature()
                    hum = sensor.humidity()
                    state = "ON" if relay.value() else "OFF"

                    print("Status requested")
                    print("Temperature:", temp, "°C")
                    print("Humidity:", hum, "%")
                    print("Relay:", state)

                    send_message(
                        "🌡 Temperature: {:.2f} °C\n"
                        "💧 Humidity: {:.2f} %\n"
                        "🔌 Relay: {}"
                        .format(temp, hum, state)
                    )

    except Exception as e:
        print("Error:", e)

    time.sleep(0.3)
