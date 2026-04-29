import os
os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"

import cv2
import requests
import threading
import http.client

FLASK_URL = "http://127.0.0.1:5001/detect"
ESP32_IP  = "192.168.18.66"

current_emotion = "..."
is_sending = False

def send_to_esp32(emotion):
    try:
        sock = __import__('socket').socket()
        sock.bind(('192.168.18.121', 0))
        sock.settimeout(10)  # ← increase from 5 to 10
        sock.connect((ESP32_IP, 80))
        req = f"GET /command?emotion={emotion} HTTP/1.1\r\nHost: {ESP32_IP}\r\nConnection: close\r\n\r\n"
        sock.send(req.encode())
        sock.recv(1024)
        sock.close()
        print(f"ESP32 OK!")
    except Exception as e:
        print(f"ESP32 error: {e}")

def send_to_flask(img_bytes):
    global current_emotion, is_sending
    is_sending = True
    try:
        response = requests.post(
            FLASK_URL,
            data=img_bytes,
            headers={"Content-Type": "image/jpeg"},
            timeout=10
        )
        current_emotion = response.text.strip()
        print(f"Emotion: {current_emotion}")
        send_to_esp32(current_emotion)
    except Exception as e:
        print(f"Flask error: {e}")
    is_sending = False

EMOTION_COLORS = {
    "happy":        (0, 255, 255),
    "sad":          (255, 0, 0),
    "angry":        (0, 0, 255),
    "fear":         (128, 0, 128),
    "surprise":     (255, 255, 255),
    "neutral":      (200, 200, 200),
    "...":          (0, 255, 0),
}

cap = cv2.VideoCapture(1)
frame_count = 0

print("Webcam starting... press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Mirror
    frame = cv2.flip(frame, 1)
    frame_count += 1

    # Send every 10 frames to Flask (like original code)
    if frame_count % 10 == 0 and not is_sending:
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_bytes = img_encoded.tobytes()
        thread = threading.Thread(target=send_to_flask, args=(img_bytes,))
        thread.daemon = True
        thread.start()

    # Show emotion on screen
    color = EMOTION_COLORS.get(current_emotion.lower(), (0, 255, 0))
    h, w = frame.shape[:2]

    # Emotion text
    cv2.putText(frame, f"Emotion: {current_emotion}",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, color, 2)

    # Analyzing indicator
    if is_sending:
        cv2.putText(frame, "analyzing...",
                    (50, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

    cv2.imshow("MoodRoom - Emotion Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()