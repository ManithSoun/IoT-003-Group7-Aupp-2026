# 🎭 MoodRoom — Smart Emotion-Based Environment System

## 1. Project Overview
MoodRoom is a smart room system that detects a person's facial emotion using an ESP32-CAM and automatically adjusts the room environment in real time. Depending on the detected emotion, the system controls an RGB LED, a servo motor, a piezo buzzer, and a Spotify playlist to create an atmosphere that matches how the person feels.

The system uses DeepFace to detect 5 core emotions: Happy, Sad, Fear, Angry, and Surprised, plus Neutral as a calm default state. The buzzer plays a short notification tone when the emotion changes, while Spotify handles the background music through the laptop speakers.

In addition to automatic detection, the system also supports manual control via a Telegram bot, allowing the user to force a capture, check the current room state, or override the music at any time.

---

## 2. Hardware Components

MoodRoom hardware is divided into **two main nodes**:

---

### 2.1 Node A — Laptop (Brain)

Node A acts as the intelligent processing center of the system.

### Core Components:
| Component | Role |
|----------|------|
| ESP32-CAM / Laptop Webcam | Captures facial image input |
| DeepFace Model | Performs facial emotion detection |
| Flask Web Server | Handles API and system communication |
| Spotify API | Controls emotion-based music playlists |
| Telegram Bot | Manual remote control and monitoring |
| MQTT Publisher | Sends emotion commands to Node B |

### Main Responsibilities:
- Capture user face
- Analyze emotion
- Select music playlist
- Send emotion state to Node B
- Notify Telegram bot
- Host dashboard interface

---

### 2.2 Node B — ESP32 (Actuators and Sensors)

Node B is the physical interaction layer that receives emotion commands and controls hardware outputs.

### Sensors:
| Component | Function |
|----------|----------|
| PIR Sensor | Detects motion / occupancy |
| IR Sensor | Additional object or presence detection |

### Actuators:
| Component | Function |
|----------|----------|
| NeoPixel 24-LED Ring | Emotion-based lighting effects |
| DC Motor + L298N | Fan speed control |
| Piezo Buzzer | Emotion sound alerts |
| OLED Display | Displays emotion + system status |

### Main Responsibilities:
- Detect room presence
- Receive MQTT emotion commands
- Control LEDs
- Run fan motor
- Display mood status
- Play sound feedback

---

## 3. System Architecture

The MoodRoom system consists of interconnected smart nodes communicating through WiFi and MQTT.

### 3.1 Node Overview

| Node | Hardware | Role |
|------|----------|------|
| Node A | Laptop + Camera | Emotion detection, AI processing, dashboard, Spotify, Telegram |
| Node B | ESP32 + Sensors/Actuators | Sensor monitoring and physical room control |

---

### 3.2 Communication Flow

1. PIR detects user presence  
2. Node A captures image  
3. DeepFace analyzes emotion  
4. Node A publishes emotion via MQTT  
5. Spotify changes playlist  
6. Telegram sends update  
7. Node B activates LED, fan, buzzer, and OLED  

---

### 3.3 MQTT Topics

| Topic | Publisher | Subscriber | Purpose |
|------|------------|-------------|---------|
| moodroom/pir | ESP32 | Laptop | Motion detection |
| moodroom/emotion | Laptop | ESP32 | Emotion command |
| moodroom/status | Laptop | Telegram | Room state |
| moodroom/mode | Telegram | Laptop | Auto/manual control |

---

### 3.4 System Architecture Diagram

![System Architecture Diagram]()

---

## 4. Software Implementation

### 4.1 File Structure

### ESP32 Firmware:
- `main.py`
- `led.py`
- `buzzer.py`
- `display.py`
- `motor.py`
- `pir.py`

### Laptop Server:
- `server.py`
- `music.py`
- `telegram_bot.py`

---

### 4.2 Key Software Features

### Emotion Detection:
- Haar Cascade face detection  
- DeepFace classification  
- Custom neutral filtering  
- Duplicate emotion suppression  

### Music Integration:
- Spotify OAuth  
- Emotion-based playlists  
- Automatic playback switching  

### Telegram Bot:
- `/start`
- `/capture`
- `/status`
- `/play`
- `/auto`
- `/room off`

---

## 5. Decision Logic

MoodRoom uses multiple sensor and AI conditions before taking action.

## Main Logic:
- PIR detects presence → Scan face  
- Emotion detected → Update environment  
- Same emotion → No change  
- No user → Shut down room  
- Manual mode → Telegram overrides AI  

---

### 5.1 Decision Flow Diagram

![System Flow Diagram]()

---

## 6. Emotion Response Table

| Emotion | LED | Fan | Buzzer | OLED | Spotify |
|--------|-----|-----|--------|------|---------|
| Happy | Yellow | Slow | 2 beeps | HAPPY | Upbeat |
| Sad | Blue | Slow | Soft tone | SAD | Lo-fi |
| Angry | Red Flash | Fast | Rapid beeps | ANGRY | Calm |
| Fear | Purple | Medium | 3 beeps | FEAR | Soothing |
| Surprise | Rainbow | Medium | Quick beeps | SURPRISE | Energetic |
| Neutral | White | Slow | Silent | NEUTRAL | Chill |
| No Person | Off | Off | Off | Blank | Paused |

---

## 7. Challenges & Solutions

### Challenge 1: DeepFace Overused Neutral  
**Solution:** Custom confidence threshold filtering  

#### Challenge 2: Poor ESP32-CAM Quality  
**Solution:** Switched to laptop webcam  

### Challenge 3: PIR False Triggers  
**Solution:** Added cooldown and debounce logic  

---

## 8. Conclusion

MoodRoom demonstrates a complete AI-powered IoT smart room system that combines:
- Computer Vision  
- Emotion Detection  
- MQTT Communication  
- Real-Time Automation  
- Remote Control  

### Key Achievements:
- Dual-node architecture  
- Real-time mood adaptation  
- Telegram + Spotify integration  
- Smart occupancy detection  
- Modular and scalable design  

The project highlights the power of combining AI with IoT to create adaptive environments that respond intelligently to human emotion.
