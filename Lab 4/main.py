from machine import Pin, I2C, ADC
import time
import ujson
import ds3231
from mlx90614 import MLX90614
from bmp280 import BMP280
import network
from umqtt.simple import MQTTClient

# WIFI
SSID     = "Roasters home"
PASSWORD = "matcha520"

# MQTT
MQTT_BROKER   = os.getenv("MQTT_BROKER")
PORT      = 1883
CLIENT_ID = b"esp32_multi_sensors"
TOPIC     = b"/aupp/esp32/multi_sensors"
KEEPALIVE = 30

# I2C SETUP
i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)

# SENSORS
rtc = ds3231.DS3231(i2c)
  # rtc.set_time(2026, 3, 9, 12, 0, 0)  # uncomment once to set time, then comment again

mlx = MLX90614(i2c)
bmp = BMP280(i2c)

  # MQ-5 Gas sensor
gas_sensor = ADC(Pin(33))
gas_sensor.atten(ADC.ATTN_11DB)
gas_sensor.width(ADC.WIDTH_12BIT)

# GAS MOVING AVERAGE STORAGE
gas_readings = []


# WIFI CONNECT
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.3)
    print("WiFi OK:", wlan.ifconfig())

# MQTT HELPERS
def make_client():
    return MQTTClient(client_id=CLIENT_ID, server=BROKER,
                      port=PORT, keepalive=KEEPALIVE)

def connect_mqtt(c):
    time.sleep(0.5)
    c.connect()
    print("MQTT connected")

# TASK 1: GAS MOVING AVERAGE
def get_gas_average():
    global gas_readings
    raw = gas_sensor.read()
    gas_readings.append(raw)
    if len(gas_readings) > 5:
        gas_readings.pop(0)
    avg = round(sum(gas_readings) / len(gas_readings), 2)
    print("Raw Gas   :", raw)
    print("Gas Avg   :", avg)
    return raw, avg

# TASK 2: GAS RISK CLASSIFICATION
def classify_gas(avg):
    if avg < 2100:
        risk = "SAFE"
    elif avg < 2600:
        risk = "WARNING"
    else:
        risk = "DANGER"
    print("Risk Level:", risk)
    return risk

# TASK 3: FEVER DETECTION
def check_fever():
    body_temp = round(mlx.read_object_temp(), 2)
    if body_temp >= 32.5:
        fever_flag = 1
    else:
        fever_flag = 0
    print("Body Temp :", body_temp, "C")
    print("Fever Flag:", fever_flag)
    return body_temp, fever_flag


# TASK 4: PRESSURE & ALTITUDE
def get_environment():
    room_temp = round(bmp.temperature, 2)
    pressure  = round(bmp.pressure / 100, 2)
    altitude  = round(bmp.altitude, 2)
    print("Room Temp :", room_temp, "C")
    print("Pressure  :", pressure, "hPa")
    print("Altitude  :", altitude, "m")
    return room_temp, pressure, altitude

# GET TIMESTAMP FROM DS3231
def get_timestamp():
    t = rtc.get_time()
    timestamp = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5])
    print("Timestamp :", timestamp)
    return timestamp

# MAIN
wifi_connect()
client = make_client()

while True:
    try:
        connect_mqtt(client)

        while True:
            print("\n----- SENSOR READING -----")

            # Task 1
            raw_gas, gas_avg = get_gas_average()

            # Task 2
            risk_level = classify_gas(gas_avg)

            # Task 3
            body_temp, fever_flag = check_fever()

            # Task 4
            room_temp, pressure, altitude = get_environment()

            # Timestamp
            timestamp = get_timestamp()

            # JSON Packet
            data = {
                "timestamp":  timestamp,
                "gas_raw":    raw_gas,
                "gas_avg":    gas_avg,
                "risk_level": risk_level,
                "body_temp":  body_temp,
                "fever_flag": fever_flag,
                "room_temp":  room_temp,
                "pressure":   pressure,
                "altitude":   altitude
            }

            json_data = ujson.dumps(data)
            print("\nJSON Packet:")
            print(json_data)
            print("-----------------------------")

            # Publish to MQTT
            client.publish(TOPIC, json_data)
            print("Published to MQTT!")

            time.sleep(5)

    except OSError as e:
        print("MQTT error:", e)
        try:
            client.close()
        except:
            pass
        print("Retrying in 3s...")
        time.sleep(3)
