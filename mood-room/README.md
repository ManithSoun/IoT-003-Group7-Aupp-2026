# 🎭 MoodRoom — Smart Emotion-Based Environment System

## 1. Project Overview
MoodRoom is a smart room system that detects a person's facial emotion using an ESP32-CAM and automatically adjusts the room environment in real time. Depending on the detected emotion, the system controls an RGB LED, a servo motor, a piezo buzzer, and a Spotify playlist to create an atmosphere that matches how the person feels.

The system uses DeepFace to detect 5 core emotions: Happy, Sad, Fear, Angry, and Surprised, plus Neutral as a calm default state. The buzzer plays a short notification tone when the emotion changes, while Spotify handles the background music through the laptop speakers.

In addition to automatic detection, the system also supports manual control via a Telegram bot, allowing the user to force a capture, check the current room state, or override the music at any time.

---

## 2. Hardware Components

MoodRoom hardware is divided into **two main nodes**:

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


### 2.2 Node B — ESP32 (Actuators and Sensors)

Node B is the physical interaction layer that receives emotion commands and controls hardware outputs.

### Sensors:
| Component | Pin | Purpose |
|---|---|---|
| PIR sensor 1 | GPIO13 | Door detection |
| IR sensor  | GPIO12 | Room presence |

### Actuators:
| Component | Pin | Purpose |
|---|---|---|
| PIR sensor 1 | GPIO13 | Door detection |
| PIR sensor 2 | GPIO12 | Room presence |
| NeoPixel 24-LED | GPIO23 | Color lighting |
| DC Motor ENA | GPIO14 | Fan speed |
| DC Motor IN1 | GPIO26 | Fan direction |
| DC Motor IN2 | GPIO27 | Fan direction |
| Buzzer | GPIO4 | Audio feedback |
| Display SDA | GPIO21 | Song info |
| Display SCL | GPIO22 | Song info |

### Main Responsibilities:
- Detect room presence
- Receive MQTT emotion commands
- Control LEDs
- Run fan motor
- Display mood status
- Play sound feedback

---

## 3. System Architecture
The diagram illustrates the overall interaction between input devices, processing units, and output components in the MoodRoom system. Sensor inputs from the PIR door sensor and IR sensor are first received by the ESP32, which acts as the main controller for hardware operations. The ESP32 communicates bidirectionally with the laptop server using MQTT, enabling data exchange and decision-making.

The ESP-CAM sends captured images directly to the laptop server, where emotion detection is performed. Based on the detected emotion, the laptop server processes the result and controls external services such as Spotify for music playback. It also communicates with the Telegram bot and web dashboard to provide user interaction and system monitoring.

After processing, commands are sent back to the ESP32, which activates output devices including the NeoPixel LED, DC motor (fan), OLED display, and buzzer. This architecture ensures real-time response, efficient communication, and seamless integration between AI processing and physical environment control.


### 3.1 Communication Flow

1. PIR detects user presence  
2. Node A captures image  
3. DeepFace analyzes emotion  
4. Node A publishes emotion via MQTT  
5. Spotify changes playlist  
6. Telegram sends update  
7. Node B activates LED, fan, buzzer, and OLED  

### 3.2 MQTT Topics

| Topic | Publisher | Subscriber | Purpose |
|------|------------|-------------|---------|
| moodroom/pir | ESP32 | Laptop | Motion detection |
| moodroom/emotion | Laptop | ESP32 | Emotion command |
| moodroom/status | Laptop | Telegram | Room state |
| moodroom/mode | Telegram | Laptop | Auto/manual control |


### 3.4 System Architecture Diagram

![System Architecture Diagram](/mood-room/assets/system_architecture.png)

---

# 4. Software Implementation

## 4.1 File Structure

The codebase is divided into two main subsystems:

### ESP32 Actuator (MicroPython)

| File              | Location        | Language    | Purpose                                                   |
|-------------------|-----------------|-------------|-----------------------------------------------------------|
| `main.py`         | esp32_actuator/ | MicroPython | Main loop: WiFi, MQTT, PIR monitoring, emotion dispatch   |
| `led.py`          | esp32_actuator/ | MicroPython | NeoPixel LED control (solid, flash, pulse, spin)          |
| `buzzer.py`       | esp32_actuator/ | MicroPython | PWM buzzer with per-emotion tone patterns                 |
| `display.py`      | esp32_actuator/ | MicroPython | SSD1306 OLED display with emotion info and status screens |
| `motor.py`        | esp32_actuator/ | MicroPython | DC motor control via L298N (slow/medium/fast)             |
| `pir.py`          | esp32_actuator/ | MicroPython | PIR sensor reading (door + room sensors)                  |
| `umqtt_simple.py` | esp32_actuator/ | MicroPython | Lightweight MQTT client for MicroPython                   |

### Laptop / Server (Python 3)

| File              | Location | Language | Purpose                                                |
|-------------------|----------|----------|--------------------------------------------------------|
| `server.py`       | laptop/  | Python 3 | Flask server + DeepFace + camera loop + MQTT + preview |
| `music.py`        | laptop/  | Python 3 | Spotipy OAuth + playlist switching per emotion         |
| `telegram_bot.py` | laptop/  | Python 3 | Telegram bot with commands and MQTT integration        |


## 4.2 ESP32 Firmware (MicroPython)

### 4.2.1 `main.py` (Core Control Loop)

The `main.py` file runs entirely on the ESP32 and handles WiFi connection, MQTT subscription, PIR monitoring, and emotion dispatching in a separate thread to avoid blocking the MQTT loop.

**Key Logic Flow:**

- On boot:
  - Display startup screen
  - Connect to WiFi
  - Show IP address on OLED
- Connect to HiveMQ public MQTT broker
- Subscribe to topic: `moodroom/emotion`
- Start `mqtt_loop()` in a background thread (polls messages every 50ms)
- Main thread continuously monitors both PIR sensors

**PIR Behavior:**

- Door PIR trigger:
  - Publish `moodroom/pir: detected`
  - Apply 15-second cooldown
- Room PIR monitoring:
  - If no motion for >15 seconds → publish `moodroom/pir: left`
  - Shut down all actuators


## 4.3 Laptop-Side Software

### 4.3.2 Emotion Detection Logic

The emotion detection pipeline in `analyze_emotion()` uses a two-stage approach to improve accuracy:

**Stage 1 — Face Detection (Haar Cascade):**

- OpenCV Haar cascade (`haarcascade_frontalface_default.xml`) detects faces
- Selects the largest detected face
- Adds 20px padding around the cropped face

**Stage 2 — Emotion Classification (DeepFace):**

- `DeepFace.analyze()` returns probabilities for 6 emotions
- Removes **neutral** from candidates initially
- Selects the highest non-neutral emotion

**Neutral Handling Rule:**

- Neutral is selected **only if** it exceeds the top emotion by **>30%**
- Prevents over-classification as neutral

**Smart Change Detection:**

- If detected emotion == current emotion → skip update
- If no face or detection fails → keep previous emotion
- Prevents unnecessary actuator switching


### 4.3.3 `music.py` — Spotify Integration

Uses the Spotipy library with SpotifyOAuth flow for playlist control. The module maintains a current_playlist_emotion global to prevent redundant API calls when the same emotion is re-detected. Playlists are curated for each emotion and played in shuffle mode. Spotify Premium is required for programmatic playback control; free accounts receive a graceful fallback.

**Emotion-Based Playlists:**

| Emotion  | Playlist Type        | Spotify URI                             |
|----------|---------------------|-----------------------------------------|
| happy    | Upbeat / high energy | spotify:playlist:0D327uChQL23ztWH2CHNdh |
| sad      | Lo-fi / melancholic  | spotify:playlist:04s3sXceiWauXzBPOqfxOX |
| angry    | Intense calm / focus | spotify:playlist:7vlxHyLBgE8EuBcZxYZyzj |
| neutral  | Chill / ambient      | spotify:playlist:0EOuwNPYzMfcemIbHoqqrj |
| surprise | Upbeat / energetic   | spotify:playlist:6MvK7J7PrO3TiNZg10tPhL |
| fear     | Soothing / calming   | spotify:playlist:3yoKElJYbFz1B140ZqClCh |


### 4.3.4 `telegram_bot.py` — Remote Control Interface

The Telegram bot provides full remote control and status monitoring of the MoodRoom system from any device. It maintains its own MQTT connection (separate client from server.py) to receive status updates and issue command

**Available Commands:**

| Command           | Mode   | Action                                              |
|-------------------|--------|-----------------------------------------------------|
| `/start`          | Any    | Show welcome message and commands                   |
| `/capture`        | Auto   | Trigger immediate face scan via PIR                 |
| `/status`         | Any    | Show system state (emotion, occupancy, music, etc.) |
| `/play [emotion]` | Manual | Switch to manual mode and set emotion               |
| `/auto`           | Auto   | Restore automatic AI-based mode                     |
| `/room off`       | Any    | Turn off all actuators and stop music               |
| `/help`           | Any    | Display all commands                                |

---

## 5. Decision Logic

MoodRoom uses multiple sensor and AI conditions before taking action.

### Primary decision logic

| Condition                     | Inputs Combined                                      | Action                                                                 |
|------------------------------|------------------------------------------------------|------------------------------------------------------------------------|
| Person at door               | PIR Door = HIGH                                      | Publish `moodroom/pir: detected` → trigger face scan                   |
| Emotion detected + person present | DeepFace result != null AND PIR Room = HIGH      | Update LED, motor, buzzer, display, Spotify, Telegram                  |
| No face found after scan     | DeepFace = null                                      | Keep current emotion — no change to actuators                          |
| Same emotion re-detected     | New emotion == current emotion                       | Skip update — no unnecessary switching                                 |
| Person left room             | PIR Room = LOW for >15 seconds                       | Shut off all actuators, publish `moodroom/pir: left`                   |
| PIR cooldown                 | Time since last scan < 15 seconds                    | Suppress re-scan to prevent rapid thrashing                            |
| Manual override              | Telegram `/play` command                             | Switch to manual mode; bypass PIR/AI pipeline entirely                 |

### 5.2 Decision Flow Diagram

![System Flow Diagram](/mood-room/assets/system_folwchart.png)

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

## 1. Emotion Over-Classification as Neutral  
During testing, the system frequently classified facial expressions as **neutral**, even when users were clearly showing emotions like happiness or sadness. This occurred because DeepFace often defaults to neutral when confidence differences between emotions are small, reducing responsiveness.

**Solution:**  
A custom filtering rule was implemented where **neutral is only selected if its confidence is at least 30% higher** than other emotions. Otherwise, the strongest non-neutral emotion is used. This improved detection accuracy and made the system more responsive.


## 2. Low-Quality Image Input from ESP32-CAM  
The ESP32-CAM produced low-resolution images (320×240) and performed poorly in low-light conditions. It also introduced network latency, which reduced real-time performance and affected emotion detection accuracy.

**Solution:**  
The ESP32-CAM was replaced with a **laptop webcam (640×480) using OpenCV**. This improved image quality, lighting performance, and removed transmission delay, resulting in faster and more accurate detection.

## 3. PIR False Triggers and Repeated Scans  
The PIR sensor was too sensitive and frequently triggered multiple times during continuous movement. This caused repeated emotion detection, unnecessary processing, and unstable system behavior.

**Solution:**  
A **15-second cooldown timer** was implemented to limit repeated triggers. Debouncing was also added to filter rapid signals, and repeated identical emotion outputs are now ignored. This improved stability and efficiency.

---

## 8. Conclusion

MoodRoom demonstrates a complete AI-powered IoT smart room system that integrates computer vision, emotion detection, MQTT communication, real-time automation, and remote control into a unified solution. The system successfully implements a dual-node architecture that enables efficient processing and coordination between components. It supports real-time mood adaptation based on detected emotions, along with Telegram and Spotify integration for enhanced user interaction and personalized feedback. Additionally, smart occupancy detection improves system efficiency by ensuring actions are only triggered when a user is present. Overall, the project is designed with a modular and scalable structure, making it easy to expand or upgrade in the future. This work highlights the effectiveness of combining AI and IoT technologies to create adaptive environments that respond intelligently to human emotions.

---
