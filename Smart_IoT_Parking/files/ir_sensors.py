# ir_sensors.py
import machine

class ParkingSlots:
    def __init__(self, ir_pins=None):
        if ir_pins is None:
            ir_pins = [32, 33, 34, 35]
        self.pins      = [machine.Pin(p, machine.Pin.IN) for p in ir_pins]
        self.num_slots = len(ir_pins)

    def is_occupied(self, slot_index):
        return self.pins[slot_index].value() == 0  # Active LOW

    def get_slot_status(self):
        return [p.value() == 0 for p in self.pins]

    def get_available_count(self):
        return sum(1 for p in self.pins if p.value() == 1)

    def get_occupied_count(self):
        return self.num_slots - self.get_available_count()

    def is_full(self):
        return self.get_available_count() == 0

    def is_empty(self):
        return self.get_occupied_count() == 0

    def print_status(self):
        statuses = self.get_slot_status()
        print("\n--- Parking Slot Status ---")
        for i, occupied in enumerate(statuses):
            print(f"  Slot {i+1}: {'OCCUPIED' if occupied else 'EMPTY'}")
        print(f"  Available: {self.get_available_count()} / {self.num_slots}")
        print("---------------------------")