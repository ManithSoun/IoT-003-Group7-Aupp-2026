import os
import threading
import time
import json
import asyncio
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import cv2
import numpy as np
from deepface import DeepFace
from music import play_playlist, sp, reset_playlist
from telegram import Bot
import paho.mqtt.client as mqtt_lib
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ===== MQTT =====
MQTT_BROKER   = os.getenv("MQTT_BROKER")
TOPIC_EMOTION = "moodroom/emotion"
TOPIC_PIR     = "moodroom/pir"
TOPIC_STATUS  = "moodroom/status"
TOPIC_SONG    = "moodroom/song"
TOPIC_MODE    = "moodroom/mode"

# ===== TELEGRAM =====
BOT_TOKEN     = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID       = os.getenv("TELEGRAM_CHAT_ID")
THREAD_ID     = 1304 

# ===== STATE =====
person_in_room  = False
current_emotion = "..."
is_auto_mode    = True
pir_door_active = False
pir_room_active = False

# ===== FACE CASCADE =====
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

LED_COLORS = {
    'happy':'Yellow','sad':'Blue','angry':'Red',
    'fear':'Purple','surprise':'Rainbow','neutral':'Soft white'
}
MUSIC_MAP = {
    'happy':'Upbeat','sad':'Lo-fi','angry':'Calm',
    'fear':'Soothing','surprise':'Upbeat','neutral':'Chill'
}

# ===== ANALYZE EMOTION =====
def analyze_emotion(frame):
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=4, minSize=(50, 50)
        )
        if len(faces) == 0:
            print("No face found")
            return None

        x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
        padding = 20
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(frame.shape[1], x + w + padding)
        y2 = min(frame.shape[0], y + h + padding)
        face_img = frame[y1:y2, x1:x2]

        result = DeepFace.analyze(
            face_img,
            actions=['emotion'],
            detector_backend='opencv',
            enforce_detection=False,
            silent=True
        )

        emotions = result[0]['emotion']
        print(f"Scores: {emotions}")

        # Boost angry with disgust
        emotions['angry'] = emotions.get('angry', 0) + (emotions.get('disgust', 0) * 0.5)

        emotions_no_neutral = {k: v for k, v in emotions.items() if k != 'neutral'}
        top_emotion = max(emotions_no_neutral, key=emotions_no_neutral.get)
        top_score   = emotions_no_neutral[top_emotion]
        neutral_score = emotions['neutral']

        print(f"Top: {top_emotion} ({top_score:.1f}%) | Neutral: {neutral_score:.1f}%")

        if neutral_score > top_score + 30:
            return 'neutral'
        return top_emotion

    except Exception as e:
        print(f"Detection error: {e}")
        return None

# ===== TELEGRAM =====
async def _send_telegram(message):
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(
            chat_id=CHAT_ID,
            message_thread_id=THREAD_ID,
            text=message
        )
        print("Telegram sent!")
    except Exception as e:
        print(f"Telegram error: {e}")

def notify_telegram(emotion):
    led   = LED_COLORS.get(emotion, 'White')
    music = MUSIC_MAP.get(emotion, 'Chill')
    asyncio.run(_send_telegram(
        f"Mood: {emotion.upper()}\n"
        f"LED: {led}\n"
        f"Music: {music} playlist"
    ))

# ===== PIR HANDLERS =====
def handle_pir():
    global person_in_room, pir_door_active
    person_in_room  = True
    pir_door_active = True
    print("PIR triggered — ready for ESP32-CAM image!")

def handle_no_person():
    global current_emotion, person_in_room, pir_door_active, pir_room_active
    person_in_room  = False
    pir_door_active = False
    pir_room_active = False
    current_emotion = "..."
    print("No person — stopping everything!")
    try:
        devices = sp.devices()
        if devices['devices']:
            sp.pause_playback(device_id=devices['devices'][0]['id'])
    except:
        pass
    reset_playlist()
    mqtt_client.publish(TOPIC_EMOTION, "off")
    mqtt_client.publish(TOPIC_STATUS, "...")

# ===== SONG LOOP =====
def publish_song_loop():
    while True:
        if person_in_room:
            try:
                current = sp.current_playback()
                if current and current['is_playing']:
                    track = current['item']
                    mqtt_client.publish(TOPIC_SONG, json.dumps({
                        "song":     track['name'],
                        "artist":   track['artists'][0]['name'],
                        "progress": current['progress_ms'],
                        "duration": track['duration_ms']
                    }))
            except Exception as e:
                print(f"Song publish error: {e}")
        time.sleep(2)

# ===== MQTT =====
def on_mqtt_message(client, userdata, message):
    global current_emotion, person_in_room, is_auto_mode
    global pir_door_active, pir_room_active

    topic = message.topic
    msg   = message.payload.decode().strip()

    if topic == TOPIC_MODE:
        is_auto_mode = (msg == "auto")
        print(f"Mode: {'Auto' if is_auto_mode else 'Manual'}")

    elif topic == TOPIC_PIR:
        if msg == "detected":
            pir_door_active = True
            pir_room_active = False
            person_in_room  = True
            if is_auto_mode:
                threading.Thread(target=handle_pir, daemon=True).start()
        elif msg == "left":
            handle_no_person()

    elif topic == TOPIC_STATUS:
        if msg not in ["...", "off"]:
            pir_room_active = True

    elif topic == TOPIC_EMOTION:
        print(f"MQTT emotion: {msg}")
        if msg == "off":
            play_playlist("off")
            pir_room_active = False
        else:
            play_playlist(msg)
            current_emotion = msg
            person_in_room  = True
            pir_room_active = True

mqtt_client = mqtt_lib.Client()

def setup_mqtt():
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.connect(MQTT_BROKER, 1883)
    mqtt_client.subscribe(TOPIC_PIR)
    mqtt_client.subscribe(TOPIC_EMOTION)
    mqtt_client.subscribe(TOPIC_STATUS)
    mqtt_client.subscribe(TOPIC_MODE)
    mqtt_client.loop_start()
    print("MQTT connected!")

# ===== FLASK ROUTES =====
@app.route('/')
def dashboard():
    return send_file('index.html')

@app.route('/test', methods=['GET'])
def test():
    return "Flask server is running!", 200

@app.route('/detect', methods=['POST'])
def detect():
    global current_emotion, person_in_room

    if not person_in_room and is_auto_mode:
        return "no person", 200

    image_bytes = request.data
    if not image_bytes:
        return "No image received", 400

    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return "Invalid image", 400

    emotion = analyze_emotion(frame)
    if emotion is None:
        return "no face", 200

    if emotion == current_emotion:
        print(f"Same emotion ({emotion}) — skipping")
        return emotion, 200

    current_emotion = emotion
    play_playlist(emotion)
    mqtt_client.publish(TOPIC_EMOTION, emotion)
    mqtt_client.publish(TOPIC_STATUS, emotion)
    print(f"Emotion: {emotion}")

    threading.Thread(target=notify_telegram, args=(emotion,), daemon=True).start()
    return emotion, 200

@app.route('/status', methods=['GET'])
def get_status():
    song_data = {}
    try:
        current = sp.current_playback()
        if current and current['is_playing']:
            track = current['item']
            song_data = {
                "song":        track['name'],
                "artist":      track['artists'][0]['name'],
                "progress_ms": current['progress_ms'],
                "duration_ms": track['duration_ms']
            }
    except Exception as e:
        print(f"Song status error: {e}")

    return jsonify({
        "emotion":        current_emotion,
        "person_in_room": person_in_room,
        "is_auto_mode":   is_auto_mode,
        "pir_door":       pir_door_active,
        "pir_room":       pir_room_active,
        **song_data
    })

@app.route('/control/emotion', methods=['POST'])
def control_emotion():
    global current_emotion, person_in_room, is_auto_mode, pir_room_active
    data    = request.json
    emotion = data.get('emotion', 'neutral')

    if emotion == 'off':
        handle_no_person()
        mqtt_client.publish(TOPIC_EMOTION, 'off')
        mqtt_client.publish(TOPIC_STATUS, 'off')
    else:
        current_emotion = emotion
        person_in_room  = True
        is_auto_mode    = False
        pir_room_active = True
        play_playlist(emotion)
        mqtt_client.publish(TOPIC_EMOTION, emotion)
        mqtt_client.publish(TOPIC_STATUS, emotion)

    return jsonify({"ok": True, "emotion": emotion})

@app.route('/control/mode', methods=['POST'])
def control_mode():
    global is_auto_mode
    data = request.json
    mode = data.get('mode', 'auto')
    is_auto_mode = (mode == 'auto')
    mqtt_client.publish(TOPIC_MODE, mode)
    return jsonify({"ok": True, "mode": mode})

@app.route('/control/capture', methods=['POST'])
def control_capture():
    threading.Thread(target=handle_pir, daemon=True).start()
    return jsonify({"ok": True})

@app.route('/no_person', methods=['GET'])
def no_person_route():
    handle_no_person()
    return "OK", 200

# ===== CAMERA PROXY =====
import urllib.request

@app.route('/camera')
def camera_proxy():
    esp32_ip = request.args.get('ip', '')
    if not esp32_ip:
        return "No IP provided", 400
    stream_url = f"http://{esp32_ip}:81/stream"

    def generate():
        try:
            with urllib.request.urlopen(stream_url, timeout=10) as response:
                while True:
                    chunk = response.read(4096)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            print(f"Camera proxy error: {e}")

    return app.response_class(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# ===== MAIN =====
if __name__ == '__main__':
    print("Starting MoodRoom server...")
    setup_mqtt()

    threading.Thread(target=publish_song_loop, daemon=True).start()

    print("Server running on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=False)