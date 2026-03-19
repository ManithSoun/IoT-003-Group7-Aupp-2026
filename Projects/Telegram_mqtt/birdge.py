# bridge.py - Run this on a Raspberry Pi or any always-on computer
import paho.mqtt.client as mqtt
import requests
import json
import threading
import time

# Telegram Config
BOT_TOKEN = "8378245115:AAEwSFBK-Noxo38CT-NS8kE4p8Ht9qMkuBA"
ALLOWED_ID = -1003859247655
BOT_TOPIC_ID = 16

# MQTT Config
MQTT_BROKER = "0.0.0.0"  # Listen on all interfaces
MQTT_PORT = 1883
MQTT_TOPIC_SEND = "parking/telegram/send"
MQTT_TOPIC_RECV = "parking/telegram/recv"

# Store last command for ESP32 to poll
last_command = None
command_lock = threading.Lock()

def on_connect(client, userdata, flags, rc):
    print(f"MQTT Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC_SEND)

def on_message(client, userdata, msg):
    """Handle messages from ESP32"""
    global last_command, command_lock
    try:
        payload = msg.payload.decode()
        print(f"From ESP32: {payload}")
        
        # Parse message
        if payload.startswith("FULL"):
            _, avail, total = payload.split("|")
            send_telegram(f"🚗 Parking FULL! ({avail}/{total})")
            
    except Exception as e:
        print(f"Error: {e}")

def send_telegram(text):
    """Send to Telegram (runs on bridge, not ESP32)"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": ALLOWED_ID,
            "text": text,
            "message_thread_id": BOT_TOPIC_ID
        }
        response = requests.post(url, json=data, timeout=5)
        print(f"Telegram sent: {response.status_code}")
    except Exception as e:
        print(f"Telegram error: {e}")

def check_telegram_commands():
    """Poll Telegram for commands (runs in separate thread)"""
    global last_command, command_lock
    last_update_id = 0
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id+1}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                for update in data.get("result", []):
                    last_update_id = update["update_id"]
                    
                    if "message" in update:
                        text = update["message"].get("text", "")
                        print(f"Telegram command: {text}")
                        
                        # Store command for ESP32
                        with command_lock:
                            last_command = text
                        
            time.sleep(1)
        except Exception as e:
            print(f"Poll error: {e}")
            time.sleep(5)

# Start MQTT broker
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)

# Start Telegram polling thread
thread = threading.Thread(target=check_telegram_commands, daemon=True)
thread.start()

# Loop forever
client.loop_forever()