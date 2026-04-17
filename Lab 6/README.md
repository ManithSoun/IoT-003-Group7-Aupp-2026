# LAB6_RFID_System

## Wiring

![wiring](/Lab%206/asset/lab6_wiring1.png)

## Setup Instructions

## Flowchart

![Diagram](/Lab%206/asset/lab6_diagram.png)

## Task1 - Read UID from RFID card

- Detect card and retrieve its unique ID (UID)

![Task 1]()

## Task 2 - Match UID with student database

- Compare UID with predefined data
- If found ->valid student
- If not -> unknown card

![Task 2]()

## Task 3 - Generate current datetime

- Format:
YYYY-MM-DD HH:MM:SS

![Task 3]()

## Task 4 - If UID is valid:

- Activate buzzer for 0.3 seconds
- Save data to SD card (CSV format):
UID, Name, StudentID, Major, DateTime
- Send data to Firestore

[Link to Task 4 demo video]()

## Task 5 - If UID is invalid:

- Activate buzzer for 3 seconds
- Display: "Unknown Card"
- Do not save or send data

[Link to Task 5 demo video]()

