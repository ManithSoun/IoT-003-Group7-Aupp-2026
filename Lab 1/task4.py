import urequests
import time
from machine import Pin
import dht

# WIFI CONFIG
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# TELEGRAM CONFIG
BOT_TOKEN = "bot_token"
CHAT_ID = "chat_id"

SEND_URL = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
GET_URL  = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

# HARDWARE
sensor = dht.DHT22(Pin(4))
relay = Pin(2, Pin.OUT)
relay.off()

# CONSTANTS
TEMP_THRESHOLD = 30
last_update_id = 0

# WIFI CONNECT
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

while not wifi.isconnected():
    time.sleep(1)

print("WiFi connected")
time.sleep(3) 

# SEND MESSAGE
def send_message(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    r = urequests.post(SEND_URL, json=payload)
    print("Telegram status:", r.status_code)
    r.close()

# MAIN LOOP
while True:
    try:
        #READ SENSOR
        sensor.measure()
        temp = sensor.temperature()
        hum = sensor.humidity()

        print("Temp:", temp, "C | Hum:", hum, "%")

        #READ TELEGRAM COMMANDS
        r = urequests.get(GET_URL + "?offset={}".format(last_update_id + 1))
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

                if text == "/on":
                    relay.on()
                    print("Relay ON by user")
                    send_message("Relay turned ON")

                elif text == "/off":
                    relay.off()
                    print("Relay OFF by user")
                    send_message("Relay turned OFF")

                elif text == "/status":
                    send_message(
                        "Temperature: {:.2f} C\nHumidity: {:.2f} %\nRelay: {}"
                        .format(temp, hum, "ON" if relay.value() else "OFF")
                    )

        #AUTOMATIC ALERT (EVERY 5s)
        if temp >= TEMP_THRESHOLD and relay.value() == 0:
            print("High temperature alert sent")
            send_message("High temperature: {:.2f} C".format(temp))

        #AUTO OFF
        if temp < TEMP_THRESHOLD and relay.value() == 1:
            relay.off()
            print("Relay auto-OFF")
            send_message("Relay auto-OFF (temperature normal)")

    except Exception as e:
        print("Error:", e)

    time.sleep(5)