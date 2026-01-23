# _IoT Lab Tasks – DHT22 & Telegram Bot_

## Wiring

![wiring](asset/wiring_diagram.png)
![wiring](asset/wiring.png)

# Configuration

![Config](asset/config.png)

## Task 1: Sensor Read & Print

- Read **DHT22** sensor data every **5 seconds**.
- Print **temperature** and **humidity** values with **2 decimal places**.
  ![Task 1](/Lab%201/asset/task1.png)

## Task 2: Telegram Send

- Implement the `send_message()` function.
- Send a **test message** to the Telegram group.

  ![Task 2](/Lab%201/asset/task2result.png)
  ![Task 2](/Lab%201/asset/task2telegram.png)

## Task 3: Bot Commands

- Implement `/status` command to reply with:
  - Current **temperature**
  - Current **humidity**
  - **Relay state**
- Implement `/on` and `/off` commands to control the relay.

  ![Task 3](/Lab%201/asset/task3.png)

## Task 4: Temperature Alert Logic

- No alert messages while **temperature < 30°C**.
- If **temperature ≥ 30°C** and **relay is OFF**:
  - Send an alert **every loop (5 seconds)** until `/on` is received.
- After receiving `/on`:
  - Stop sending alerts.
- When **temperature < 30°C**:

  - Automatically turn the relay **OFF**.
  - Send a **one-time "auto-OFF"** notification.

  ## Flowchart

  ![Task4](asset/flowchart.png)

  ## Video Demo

  [Click here to view demo video](https://youtu.be/qg2fIZ6nbvY)
