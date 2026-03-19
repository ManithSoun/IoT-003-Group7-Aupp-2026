# lcd_display.py
from machine import I2C, Pin
from machine_i2c_lcd import I2cLcd

class ParkingLCD:
    def __init__(self, sda_pin=21, scl_pin=22, address=0x27, cols=16, rows=2):
        i2c      = I2C(0, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400000)
        self.lcd = I2cLcd(i2c, address, rows, cols)
        self.cols = cols
        self.rows = rows
        self.show_welcome()

    def _print_row(self, text, row):
        text = str(text)
        if len(text) < self.cols:
            text = text + " " * (self.cols - len(text))
        text = text[:self.cols]
        self.lcd.move_to(0, row)
        self.lcd.putstr(text)

    def clear(self):
        self.lcd.clear()

    def show_welcome(self):
        self._print_row(" Smart Parking ", row=0)
        self._print_row("  System Ready ", row=1)

    def show_status(self, available, total, entry_gate, exit_gate):
        self._print_row(f"Available: {available}", row=0)
        self._print_row(f"EN:{entry_gate[:4]} EX:{exit_gate[:4]}", row=1)

    def show_vehicle_entering(self):
        self._print_row(" Vehicle Entry ", row=0)
        self._print_row(" Opening Gate..", row=1)

    def show_vehicle_exiting(self):
        self._print_row(" Vehicle Exit  ", row=0)
        self._print_row(" Opening Gate..", row=1)

    def show_full(self):
        self._print_row(" Parking  FULL ", row=0)
        self._print_row(" No Slots Avail", row=1)

    def show_temp(self, temp, humidity):
        self._print_row(f"Temp:  {temp}C", row=0)
        self._print_row(f"Humid: {humidity}%", row=1)

    def show_gate_command(self, gate, action):
        self._print_row(f"{gate} Gate:", row=0)
        self._print_row(f"  {action}", row=1)

    def show_lights(self, state):
        self._print_row(" Parking Lights", row=0)
        self._print_row(f"    {state}", row=1)

    def show_message(self, line1="", line2=""):
        self._print_row(line1, row=0)
        self._print_row(line2, row=1)