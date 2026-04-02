# LAB5_Smart_Color_Detection_&_Control_with_MIT_App

## Wiring

![wiring](asset/wiringdiagram.png)
![wiring](asset/wiring.png)

## Setup Instructions

## Task1 - RGB Reading
- Read RGB values from TCS34725.
- Print values to Serial Monitor.

![Task 1]()

## Task 2 - Color Classification
- Classification Rules:
    - R > G and R > B → RED
    - G > R and G > B → GREEN
    - B > R and B > G → BLUE

[Task 2 demo video]()

## Task 3 - NeoPixel Control
- RED → NeoPixel shows Red
- GREEN → NeoPixel shows Green
- BLUE → NeoPixel shows Blue

[Task 3 demo video]()

## Task 4 - Motor Control (PWM)
- RED → PWM = 700
- GREEN → PWM = 500
- BLUE → PWM = 300

[Task 3 demo video]()

## Task 5 - MIT App Integration
- App Requirements:
    - Display detected color (Label).
    - Buttons: Forward, Stop, Backward.
    - RGB input boxes (R, G, B).
    - Button to set NeoPixel color manually.

![Task 5]()