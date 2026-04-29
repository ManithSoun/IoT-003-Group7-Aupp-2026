from machine import Pin

PIR_DOOR = Pin(13, Pin.IN, Pin.PULL_DOWN)
PIR_ROOM = Pin(12, Pin.IN, Pin.PULL_DOWN)

def person_at_door():
    return PIR_DOOR.value() == 1

def person_in_room():
    return PIR_ROOM.value() == 1