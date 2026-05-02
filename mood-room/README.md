# 🎭 MoodRoom — Smart Emotion-Based Environment System

## 1. Project Overview
MoodRoom is a smart room system that detects a person's facial emotion using an ESP32-CAM and automatically adjusts the room environment in real time. Depending on the detected emotion, the system controls an RGB LED, a servo motor, a piezo buzzer, and a Spotify playlist to create an atmosphere that matches how the person feels.

The system uses DeepFace to detect 5 core emotions: Happy, Sad, Fear, Angry, and Surprised, plus Neutral as a calm default state. The buzzer plays a short notification tone when the emotion changes, while Spotify handles the background music through the laptop speakers.

In addition to automatic detection, the system also supports manual control via a Telegram bot, allowing the user to force a capture, check the current room state, or override the music at any time.

---

## 2. Hardware Component

The MoodRoom system is composed of three interconnected nodes that communicate through WiFi and MQTT.
