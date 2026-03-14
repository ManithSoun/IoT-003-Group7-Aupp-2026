# gate_control.py
import machine
import time

class Ultrasonic:
    def __init__(self, trig_pin, echo_pin, name="Sensor"):
        self.trig = machine.Pin(trig_pin, machine.Pin.OUT)
        self.echo = machine.Pin(echo_pin, machine.Pin.IN)
        self.name = name
        self.trig.value(0)
        time.sleep_ms(100)

    def get_distance_cm(self):
        self.trig.value(0)
        time.sleep_us(5)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        timeout = time.ticks_us()
        while self.echo.value() == 0:
            if time.ticks_diff(time.ticks_us(), timeout) > 30000:
                return None

        start = time.ticks_us()
        while self.echo.value() == 1:
            if time.ticks_diff(time.ticks_us(), start) > 30000:
                return None

        duration = time.ticks_diff(time.ticks_us(), start)
        return round((duration * 0.0343) / 2, 1)

    def vehicle_detected(self, min_cm=2, max_cm=8):
        dist = self.get_distance_cm()
        if dist is None:
            return False
        return min_cm <= dist <= max_cm


class Gate:
    def __init__(self, signal_pin, name="Gate"):
        self.name = name
        self.pwm  = machine.PWM(machine.Pin(signal_pin), freq=50)
        self.is_open = False
        self._auto_close_time = None
        self.close()

    def _set_angle(self, angle):
        duty = int(40 + (angle / 180) * 75)
        self.pwm.duty(duty)
        time.sleep_ms(500)

    def open(self):
        if not self.is_open:
            print(f"[{self.name}] Opening gate...")
            self._set_angle(90)
            self.is_open = True
            self._auto_close_time = None
            print(f"[{self.name}] Gate OPEN ✅")

    def close(self):
        self._set_angle(0)
        self.is_open = False
        self._auto_close_time = None
        print(f"[{self.name}] Gate CLOSED 🔒")

    def toggle(self):
        if self.is_open:
            self.close()
        else:
            self.open()

    def open_with_auto_close(self, delay_seconds=5):
        self.open()
        self._auto_close_time = time.ticks_ms() + (delay_seconds * 1000)
        print(f"[{self.name}] Auto-closing in {delay_seconds}s...")

    def tick(self):
        if self._auto_close_time is None:
            return
        if self.is_open and time.ticks_diff(time.ticks_ms(), self._auto_close_time) >= 0:
            print(f"[{self.name}] Auto-closing now.")
            self.close()

    def get_status(self):
        return "OPEN" if self.is_open else "CLOSED"


def read_both_sensors(entry_sensor, exit_sensor, delay_ms=60):
    entry_dist = entry_sensor.get_distance_cm()
    time.sleep_ms(delay_ms)
    exit_dist  = exit_sensor.get_distance_cm()
    time.sleep_ms(delay_ms)
    return entry_dist, exit_dist