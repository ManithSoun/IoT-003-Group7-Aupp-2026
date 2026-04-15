from flask import Flask, request
import cv2
import numpy as np
from deepface import DeepFace
import requests

app = Flask(__name__)

ESP32_IP = "192.168.1.100"
ESP32_URL = f"http://{ESP32_IP}/command"

EMOTION_MAP = {
    "happy":    {"led": "yellow", "fan": "off",  "tone": "upbeat"},
    "sad":      {"led": "blue",   "fan": "off",  "tone": "slow"},
    "angry":    {"led": "red",    "fan": "high", "tone": "alert"},
    "neutral":  {"led": "white",  "fan": "off",  "tone": "none"},
    "fear":     {"led": "green",  "fan": "low",  "tone": "calm"},
    "surprise": {"led": "yellow", "fan": "off",  "tone": "upbeat"},
}

def analyze_emotion(image_bytes):
    np_arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    try:
        result = DeepFace.analyze(
            img,
            actions=['emotion'],
            enforce_detection=False
        )
        emotion = result[0]['dominant_emotion']
        print(f"Detected: {emotion}")
        return emotion
    except Exception as e:
        print(f"Detection error: {e}")
        return "neutral"

def send_to_esp32(emotion):
    try:
        response = requests.get(
            ESP32_URL,
            params={"emotion": emotion},
            timeout=2
        )
        print(f"ESP32 response: {response.status_code}")
    except Exception as e:
        print(f"ESP32 not reachable yet: {e}")

@app.route('/detect', methods=['POST'])
def detect():
    image_bytes = request.data
    if not image_bytes:
        return "No image received", 400
    emotion = analyze_emotion(image_bytes)
    
    # Trigger Spotify and ESP32 simultaneously
    play_playlist(emotion)
    send_to_esp32(emotion)

    return emotion, 200

@app.route('/test', methods=['GET'])
def test():
    return "Flask server is running!", 200

if __name__ == '__main__':
    print("Starting mood room server...")
    print("Waiting for ESP32-CAM images on port 5000")
    app.run(host='0.0.0.0', port=5001, debug=True)