import network
import time
import led
import buzzer
import display
import motor
from pir import person_at_door, person_in_room
from umqtt_simple import MQTTClient
import _thread

WIFI_SSID     = "wifi name"
WIFI_PASSWORD = "password"
MQTT_BROKER   = "broker.hivemq.com"
MQTT_CLIENT   = "moodroom_esp32_002"
TOPIC_EMOTION = b"moodroom/emotion"
TOPIC_PIR     = b"moodroom/pir"

mqtt_client = None
current_emotion = "neutral"

# Add these globals at the top
person_was_present = False
last_detected = 0
person_absent_since = 0

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print("Connecting to WiFi", end="")
    for _ in range(20):
        if wlan.isconnected():
            break
        print(".", end="")
        time.sleep(0.5)
    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"\nWiFi connected! IP: {ip}")
        return ip
    print("\nWiFi failed!")
    return None

def handle_emotion(emotion):
    global current_emotion
    print(f"Handling: {emotion}")
    current_emotion = emotion
    display.show(emotion)
    if emotion == "happy":
        led.solid(255, 200, 0)
        motor.slow()
        buzzer.happy_tone()
    elif emotion == "sad":
        led.solid(0, 0, 255)
        motor.slow()
        buzzer.sad_tone()
    elif emotion == "angry":
        led.flash(255, 0, 0)
        motor.fast()
        buzzer.angry_tone()
    elif emotion == "fear":
        led.solid(128, 0, 128)
        motor.medium()
        buzzer.fear_tone()
    elif emotion == "surprise":
        led.flash(255, 255, 255)
        motor.medium()
        buzzer.surprise_tone()
    elif emotion == "neutral":
        led.solid(200, 200, 200)
        motor.slow()
        buzzer.neutral_tone()
    elif emotion == "off":
        led.off()
        buzzer.off()
        display.off()
        motor.off()

def on_message(topic, msg):
    emotion = msg.decode().strip()
    print(f"MQTT received: {emotion}")
    _thread.start_new_thread(handle_emotion, (emotion,))

def mqtt_loop():
    global mqtt_client
    while True:
        try:
            mqtt_client.check_msg()
        except Exception as e:
            print(f"MQTT error: {e}")
            try:
                mqtt_client.connect()
                mqtt_client.subscribe(TOPIC_EMOTION)
                print("MQTT reconnected!")
            except:
                pass
        time.sleep(0.05)

def main():
    global mqtt_client

    display.startup()
    led.solid(0, 50, 50)
    time.sleep(1)
    led.off()

    ip = connect_wifi()
    if not ip:
        display.wifi_fail()
        led.flash(255, 0, 0, 5)
        return

    display.wifi_ok(ip)
    led.solid(0, 255, 0)
    time.sleep(2)
    led.off()

    print("Connecting to MQTT broker...")
    mqtt_client = MQTTClient(MQTT_CLIENT, MQTT_BROKER)
    mqtt_client.set_callback(on_message)
    mqtt_client.connect()
    mqtt_client.subscribe(TOPIC_EMOTION)
    print("MQTT connected!")

    _thread.start_new_thread(mqtt_loop, ())

    person_was_present = False
    last_detected = 0
    COOLDOWN = 15
    DEBOUNCE = 15
    person_absent_since = 0

    print("Monitoring PIR...")

    while True:
        now = time.time()

        # PIR 1 — door triggers face scan
        if person_at_door() or person_in_room():
            if not person_was_present:
                print("Person at door! Scanning...")
                person_was_present = True
                last_detected = now
                mqtt_client.publish(TOPIC_PIR, b"detected")
            elif now - last_detected > COOLDOWN:
                print("Re-scanning emotion...")
                mqtt_client.publish(TOPIC_PIR, b"detected")
                last_detected = now

        # PIR 2 — room monitors presence
        if person_in_room():
            person_absent_since = 0
        else:
            if person_was_present:
                if person_absent_since == 0:
                    person_absent_since = now
                if now - person_absent_since > DEBOUNCE:
                    print("Person left room!")
                    led.off()
                    buzzer.off()
                    display.off()
                    motor.off()
                    mqtt_client.publish(TOPIC_PIR, b"left")
                    person_was_present = False
                    person_absent_since = 0

        time.sleep(0.1)

main()
