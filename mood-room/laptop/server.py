import os
import socket
import threading
import time
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

from flask import Flask, request
from flask_cors import CORS
import cv2
import numpy as np
from deepface import DeepFace
from music import play_playlist, sp
import asyncio
from telegram import Bot
import paho.mqtt.client as mqtt_lib

app = Flask(__name__)
CORS(app)

MQTT_BROKER   = "broker.hivemq.com"
TOPIC_EMOTION = "moodroom/emotion"
TOPIC_PIR     = "moodroom/pir"

TOPIC_STATUS = "moodroom/status"

BOT_TOKEN = "YOUR_NEW_BOT_TOKEN"
CHAT_ID   = -1003859247655
THREAD_ID = 1304

# Shared frame
latest_frame = None
frame_lock = threading.Lock()
person_in_room = False
current_emotion = "..."
is_auto_mode = True

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ===== CAMERA LOOP =====
def camera_loop():
    global latest_frame
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    for _ in range(10):
        cap.read()
    while True:
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            with frame_lock:
                latest_frame = frame.copy()

# ===== GET BEST FRAME =====
def get_best_frame():
    best_frame = None
    best_face_size = 0
    for _ in range(10):  # ← reduce from 20 to 10
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()
            else:
                time.sleep(0.03)
                continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.2,  # ← increase for speed
            minNeighbors=3,          # ← reduce for speed
            minSize=(50, 50)
        )
        if len(faces) > 0:
            biggest = max(faces, key=lambda f: f[2]*f[3])
            size = biggest[2] * biggest[3]
            if size > best_face_size:
                best_face_size = size
                best_frame = frame.copy()
        time.sleep(0.02)  # ← reduce from 0.03
    return best_frame

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

        # Get all emotion scores
        emotions = result[0]['emotion']
        print(f"Scores: {emotions}")

        # Remove neutral and pick highest remaining
        emotions_no_neutral = {k: v for k, v in emotions.items() if k != 'neutral'}
        top_emotion = max(emotions_no_neutral, key=emotions_no_neutral.get)
        top_score = emotions_no_neutral[top_emotion]
        neutral_score = emotions['neutral']

        print(f"Top: {top_emotion} ({top_score:.1f}%) | Neutral: {neutral_score:.1f}%")

        # Only return neutral if it's MUCH higher than others
        if neutral_score > top_score + 30:  # neutral wins only if 30% more confident
            return 'neutral'
        else:
            return top_emotion

    except Exception as e:
        print(f"Detection error: {e}")
        return None

def show_preview():
    while True:
        with frame_lock:
            if latest_frame is None:
                time.sleep(0.01)
                continue
            frame = latest_frame.copy()

        # Check frame is valid before processing
        if frame is None or frame.size == 0:
            continue

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Check gray frame is valid
            if gray is None or gray.size == 0:
                continue

            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=4, minSize=(50, 50)
            )

            display_emotion = current_emotion if person_in_room else "No one here"

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, display_emotion.upper(),
                            (x, y-10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.8, (0, 255, 0), 2)

            cv2.putText(frame, f"Faces: {len(faces)}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Mood: {display_emotion.upper()}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Room: {'IN' if person_in_room else 'EMPTY'}",
                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 0) if person_in_room else (0, 0, 255), 2)

            cv2.imshow("MoodRoom", frame)

        except Exception as e:
            print(f"Preview error: {e}")
            continue

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

# ===== TELEGRAM =====
LED_COLORS = {'happy':'Yellow','sad':'Blue','angry':'Red','fear':'Purple','surprise':'White','neutral':'White'}
MUSIC_MAP  = {'happy':'Upbeat','sad':'Lo-fi','angry':'Calm','fear':'Soothing','surprise':'Upbeat','neutral':'Chill'}

async def send_telegram(message):
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
    asyncio.run(send_telegram(
        f"🎭 Mood: {emotion.upper()}\n"
        f"💡 LED: {LED_COLORS.get(emotion,'White')}\n"
        f"🎵 Music: {MUSIC_MAP.get(emotion,'Chill')} playlist"
    ))

# ===== PIR HANDLER =====
def handle_pir():
    global current_emotion, person_in_room
    person_in_room = True  # keep this True during rescan!
    print("Scanning face...")

    frame = get_best_frame()
    if frame is None:
        print("No face found — keeping current emotion")
        return  # ← don't change anything if no face!

    emotion = analyze_emotion(frame)
    if emotion is None:
        print("No emotion — keeping current")
        return  # ← keep current emotion!

    if emotion == current_emotion:
        print(f"Same emotion ({emotion}) — skipping")
        return  # ← no need to update if same!

    current_emotion = emotion
    play_playlist(emotion)
    mqtt_client.publish(TOPIC_EMOTION, emotion)
    mqtt_client.publish(TOPIC_STATUS, emotion)
    print(f"Emotion changed to: {emotion}")
    threading.Thread(target=notify_telegram, args=(emotion,), daemon=True).start()

def handle_no_person():
    global current_emotion, person_in_room
    person_in_room = False
    current_emotion = "..."
    print("No person — stopping")

# ===== MQTT =====
def on_pir_message(client, userdata, message):
    msg = message.payload.decode()
    print(f"PIR MQTT: {msg}")
    if msg == "detected":
        threading.Thread(target=handle_pir, daemon=True).start()
    elif msg == "left":
        handle_no_person()

mqtt_client = mqtt_lib.Client()

def on_mqtt_message(client, userdata, message):
    global current_emotion, person_in_room, is_auto_mode
    topic = message.topic
    msg   = message.payload.decode().strip()

    if topic == "moodroom/mode":
        is_auto_mode = (msg == "auto")
        print(f"Mode: {'Auto' if is_auto_mode else 'Manual'}")

    elif topic == TOPIC_PIR:
        if msg == "detected":
            if is_auto_mode:  # ← only auto scan if in auto mode!
                threading.Thread(target=handle_pir, daemon=True).start()
        elif msg == "left":
            if is_auto_mode:  # ← only stop if in auto mode!
                handle_no_person()

    elif topic == TOPIC_EMOTION:
        print(f"Manual emotion: {msg}")
        if msg == "off":
            play_playlist("off")
        else:
            play_playlist(msg)
            current_emotion = msg
            person_in_room  = True

def setup_mqtt():
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.connect(MQTT_BROKER, 1883)
    mqtt_client.subscribe(TOPIC_PIR)
    mqtt_client.subscribe(TOPIC_EMOTION)
    mqtt_client.subscribe("moodroom/mode")  # ← add this!
    mqtt_client.loop_start()
    print("MQTT connected!")

# ===== FLASK ROUTES =====
@app.route('/test', methods=['GET'])
def test():
    return "Flask server is running!", 200

@app.route('/detect', methods=['POST'])
def detect():
    image_bytes = request.data
    if not image_bytes:
        return "No image received", 400
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    emotion = analyze_emotion(frame)
    if emotion:
        play_playlist(emotion)
        mqtt_client.publish(TOPIC_EMOTION, emotion)
    return emotion or "neutral", 200

# ===== MAIN =====
if __name__ == '__main__':
    print("Starting MoodRoom server...")

    setup_mqtt()

    cam_thread = threading.Thread(target=camera_loop, daemon=True)
    cam_thread.start()

    flask_thread = threading.Thread(
        target=lambda: app.run(
            host='0.0.0.0', port=5001,
            debug=False, use_reloader=False
        ),
        daemon=True
    )
    flask_thread.start()

    show_preview()