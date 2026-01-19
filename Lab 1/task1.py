import time
from machine import Pin
import dht

# DHT22 connected to GPIO4 (D4)
sensor = dht.DHT22(Pin(4))

while True:
    try:
        sensor.measure()
        temperature = sensor.temperature()
        humidity = sensor.humidity()

        print("Temperature: {:.2f} °C".format(temperature))
        print("Humidity: {:.2f} %".format(humidity))
        print("---------------------------")

    except Exception as e:
        print("Sensor error:", e)

    time.sleep(5)