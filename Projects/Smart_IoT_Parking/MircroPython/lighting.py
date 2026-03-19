# lighting.py
import machine
import time

class Lighting:
    def __init__(self, led_pin=2):
        self.led         = machine.Pin(led_pin, machine.Pin.OUT)
        self.led_state   = False
        self.auto_mode   = True
        self.led_off()

    def lights_on(self):
        self.led_on()
        print("[Lighting] Lights ON")

    def lights_off(self):
        self.led_off()
        print("[Lighting] Lights OFF")

    def get_relay_status(self):
        return "ON" if self.led_state else "OFF"

    def led_on(self):
        self.led.value(1)
        self.led_state = True

    def led_off(self):
        self.led.value(0)
        self.led_state = False

    def led_blink(self, times=3, interval_ms=200):
        for _ in range(times):
            self.led.value(1)
            time.sleep_ms(interval_ms)
            self.led.value(0)
            time.sleep_ms(interval_ms)
        self.led.value(1 if self.led_state else 0)

    def toggle_lights(self):
        if self.led_state:
            self.lights_off()
        else:
            self.lights_on()

    def set_auto_mode(self, enabled):
        self.auto_mode = enabled
        print(f"[Lighting] Mode: {'AUTO' if enabled else 'MANUAL'}")

    def get_status(self):
        return {
            "lights"   : self.get_relay_status(),
            "auto_mode": self.auto_mode
        }