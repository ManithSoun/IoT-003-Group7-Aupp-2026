# blynk.py
import urequests
import gc
import time

BLYNK_API   = "http://blynk.cloud/external/api"
BLYNK_TOKEN = "_Hd_bbf5jAZ6LVWl9opiATjSDK4dXgXQ"

# Track last known button states
_last_v0 = "0"
_last_v3 = "0"
_last_v4 = "0"

def blynk_set(pin, value):
    gc.collect()
    try:
        url = f"{BLYNK_API}/update?token={BLYNK_TOKEN}&v{pin}={value}"
        r   = urequests.get(url, timeout=5)
        print(f"[Blynk] V{pin}={value} status:{r.status_code}")
        r.close()
        del r
        gc.collect()
        time.sleep_ms(500)
    except Exception as e:
        print(f"[Blynk] Error V{pin}: {e}")
        gc.collect()

def blynk_get(pin):
    gc.collect()
    try:
        url = f"{BLYNK_API}/get?token={BLYNK_TOKEN}&v{pin}"
        r   = urequests.get(url, timeout=5)
        val = r.text.strip()
        r.close()
        del r
        gc.collect()
        time.sleep_ms(500)
        return val
    except Exception as e:
        print(f"[Blynk] Get error V{pin}: {e}")
        gc.collect()
        return None

def blynk_update(tm, dht, entry_gate, exit_gate, lighting):
    """Push all sensor data to Blynk."""
    available = tm.get_available_count()
    temp, _   = dht.read()
    if temp is not None and temp > 50:
        temp = None  # discard bad reading
    blynk_set(1, temp if temp is not None else 0)
    time.sleep_ms(300)
    blynk_set(2, available)
    blynk_set(0, 1 if entry_gate.is_open else 0)
    time.sleep_ms(300)
    time.sleep_ms(300)
    blynk_set(3, 1 if exit_gate.is_open else 0)
    time.sleep_ms(300)
    blynk_set(4, 1 if lighting.relay_state else 0)

def blynk_check_buttons(entry_gate, exit_gate, lighting, lcd, gate_delay=5):
    global _last_v0, _last_v3, _last_v4

    # V0 — Entry gate
    v0 = blynk_get(0)
    print(f"[Blynk] V0={v0} last={_last_v0}")
    if v0 is not None and v0 != _last_v0:
        _last_v0 = v0
        if v0 == "1" and not entry_gate.is_open:
            lcd.show_vehicle_entering()
            entry_gate.open()
            print("[Blynk] Entry gate opened manually")
        elif v0 == "0" and entry_gate.is_open:
            entry_gate.close()
            print("[Blynk] Entry gate closed manually")

    time.sleep_ms(300)

    # V3 — Exit gate
    v3 = blynk_get(3)
    print(f"[Blynk] V3={v3} last={_last_v3}")
    if v3 is not None and v3 != _last_v3:
        _last_v3 = v3
        if v3 == "1" and not exit_gate.is_open:
            lcd.show_vehicle_exiting()
            exit_gate.open()
            print("[Blynk] Exit gate opened manually")
        elif v3 == "0" and exit_gate.is_open:
            exit_gate.close()
            print("[Blynk] Exit gate closed manually")

    time.sleep_ms(300)

    # V4 — Lights
    v4 = blynk_get(4)
    print(f"[Blynk] V4={v4} last={_last_v4}")
    if v4 is not None and v4 != _last_v4:
        _last_v4 = v4
        if v4 == "1" and not lighting.relay_state:
            lighting.set_auto_mode(False)
            lighting.lights_on()
            lighting.led_on()
            print("[Blynk] Lights ON")
        elif v4 == "0" and lighting.relay_state:
            lighting.set_auto_mode(False)
            lighting.lights_off()
            lighting.led_off()
            print("[Blynk] Lights OFF")
