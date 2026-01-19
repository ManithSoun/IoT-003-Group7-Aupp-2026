import urequests
import time
import network
from machine import Pin
import dht

# ======================
# WIFI CONFIG
# ======================
SSID = "Robotic WIFI"
PASSWORD = "rbtWIFI@2025"

# ======================
# TELEGRAM CONFIG
# ======================
BOT_TOKEN = "8378245115:AAEwSFBK-Noxo38CT-NS8kE4p8Ht9qMkuBA"
CHAT_ID = "-5280207636"

SEND_URL = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
GET_URL  = "https://api.telegram.org/bot{}/getUpdates".format(BOT_TOKEN)

# ======================
# HARDWARE SETUP
# ======================
sensor = dht.DHT22(Pin(4))  # DHT22 on D4
relay = Pin(2, Pin.OUT)     # Relay on D2
relay.off()

# ======================
# WIFI CONNECT
# ======================
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(SSID, PASSWORD)

while not wifi.isconnected():
    time.sleep(1)

print("WiFi connected")

# ======================
# SEND MESSAGE FUNCTION
# ======================
def send_message(text):
    payload = {"chat_id": CHAT_ID, "text": text}
    r = urequests.post(SEND_URL, json=payload)
    r.close()

# ======================
# MAIN LOOP
# ======================
last_update_id = 0
alerting = False  # Track high-temp alerts

while True:
    try:
        # -------- Telegram polling (commands only) --------
        r = urequests.get(GET_URL + "?offset={}".format(last_update_id + 1))
        data = r.json()
        r.close()

        updates = data.get("result", [])
        for upd in updates:
            last_update_id = upd["update_id"]
            msg = upd.get("message")
            if not msg:
                continue

            text = msg.get("text", "")
            chat_id = msg["chat"]["id"]
            if str(chat_id) == CHAT_ID:
                print("Command received:", text)

                if text == "/on":
                    relay.on()
                    alerting = False
                    print("Relay turned ON")
                    send_message("✅ Relay turned ON")

                elif text == "/off":
                    relay.off()
                    print("Relay turned OFF")
                    send_message("❌ Relay turned OFF")

                elif text == "/status":
                    sensor.measure()
                    temp = sensor.temperature()
                    hum = sensor.humidity()
                    state = "ON" if relay.value() else "OFF"
                    send_message(
                        "🌡 Temp: {:.2f} °C\n"
                        "💧 Humidity: {:.2f} %\n"
                        "🔌 Relay: {}"
                        .format(temp, hum, state)
                    )

        # -------- Temperature-based alerts (always run) --------
        sensor.measure()
        temp = sensor.temperature()

        # High temp alert
        if temp >= 30 and not relay.value():
            send_message("⚠️ ALERT! Temperature {:.2f}°C. Relay is OFF!".format(temp))
            alerting = True

        # Auto turn-off
        elif temp < 30 and relay.value():
            relay.off()
            send_message("ℹ️ Auto-OFF: Temperature dropped below 30°C")
            alerting = False

    except Exception as e:
        print("Error:", e)

    time.sleep(0.3)
