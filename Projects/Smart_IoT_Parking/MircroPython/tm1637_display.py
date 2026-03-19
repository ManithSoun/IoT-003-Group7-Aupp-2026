# tm1637_display.py
import machine
from tm1637 import TM1637

class SlotDisplay:
    def __init__(self, clk_pin=14, dio_pin=27, ir_pins=None, brightness=5):
        if ir_pins is None:
            ir_pins = [32, 33, 34, 35]
        self.ir_pins         = [machine.Pin(p, machine.Pin.IN) for p in ir_pins]
        self.num_slots       = len(ir_pins)
        self.display         = TM1637(clk_pin=clk_pin, dio_pin=dio_pin, brightness=brightness)
        self._last_available = -1

    def get_available_count(self):
        return sum(p.value() for p in self.ir_pins)

    def get_occupied_count(self):
        return self.num_slots - self.get_available_count()

    def is_full(self):
        return self.get_available_count() == 0

    def is_empty(self):
        return self.get_occupied_count() == 0

    def get_slot_status(self):
        return [p.value() == 0 for p in self.ir_pins]

    def get_status_dict(self):
        statuses = self.get_slot_status()
        return {
            "slots"    : [{"slot": i+1, "occupied": statuses[i]} for i in range(self.num_slots)],
            "available": self.get_available_count(),
            "total"    : self.num_slots,
            "full"     : self.is_full()
        }

    def update(self):
        available = self.get_available_count()
        if available != self._last_available:  
            self.display.show_digit(available)
            self._last_available = available
            print(f"[TM1637] Slots: {available} / {self.num_slots} available")
        return available

    def print_status(self):
        statuses = self.get_slot_status()
        print("\n--- Parking Slot Status ---")
        for i, occupied in enumerate(statuses):
            print(f"  Slot {i+1}: {'OCCUPIED' if occupied else 'EMPTY'}")
        print(f"  Available: {self.get_available_count()} / {self.num_slots}")
        print("---------------------------")
