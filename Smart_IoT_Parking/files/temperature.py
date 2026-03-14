# temperature.py
import dht
import machine
import time

class TemperatureSensor:
    def __init__(self, data_pin=4):
        self.sensor        = dht.DHT11(machine.Pin(data_pin))
        self.last_temp     = None
        self.last_humidity = None
        self.last_read_time = 0

    def read(self):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_read_time) < 1000:
            return self.last_temp, self.last_humidity
        try:
            self.sensor.measure()
            self.last_temp     = self.sensor.temperature()
            self.last_humidity = self.sensor.humidity()
            self.last_read_time = now
            return self.last_temp, self.last_humidity
        except OSError as e:
            print(f"[DHT11] Read error: {e}")
            return None, None

    def get_temperature(self):
        temp, _ = self.read()
        return temp

    def get_humidity(self):
        _, hum = self.read()
        return hum

    def get_formatted(self):
        temp, hum = self.read()
        if temp is None:
            return "Sensor Error"
        return f"Temp:{temp}C Hum:{hum}%"