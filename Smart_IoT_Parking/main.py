# main.py
import network
import time
import gc
from gate_control   import Ultrasonic, Gate, read_both_sensors
from tm1637_display import SlotDisplay
from lcd_display    import ParkingLCD
from temperature    import TemperatureSensor
from lighting       import Lighting
from telegram_bot   import telegram_send, telegram_flush_old_updates, telegram_process
from blynk          import blynk_update, blynk_check_buttons
from web_server     import web_start, web_serve

# ─── CONFIG ───────────────────────────────────────────────────────────────
WIFI_SSID  = "CINNAMON CAFE & BISTRO"
WIFI_PASS  = "cinnamoncafe"

ENTRY_TRIG = 5
ENTRY_ECHO = 18
EXIT_TRIG  = 19
EXIT_ECHO  = 23
ENTRY_SERVO= 13
EXIT_SERVO = 12
IR_PINS    = [32, 33, 34, 35]
DHT_PIN    = 4
LED_PIN    = 2
TM_CLK     = 14
TM_DIO     = 27
LCD_SDA    = 21
LCD_SCL    = 22
LCD_ADDR   = 0x27

MIN_CM     = 2
MAX_CM     = 8
GATE_DELAY = 5
NIGHT_TEMP = 30

# ─── WIFI ─────────────────────────────────────────────────────────────────
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f"Connecting to {WIFI_SSID}...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        timeout = 15
        while not wlan.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            print(".", end="")
    if wlan.isconnected():
        print(f"\nWiFi OK! IP: {wlan.ifconfig()[0]}")
        return wlan.ifconfig()[0]
    print("\nWiFi failed.")
    return None

def check_wifi():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("[WiFi] Reconnecting...")
        connect_wifi()

# ─── LIGHTING ─────────────────────────────────────────────────────────────
def smart_lighting(lighting, temp):
    if not lighting.auto_mode:
        return
    if temp is None:
        return
    if temp < NIGHT_TEMP:
        if not lighting.relay_state:
            lighting.lights_on()
            lighting.led_on()
            print(f"[Lighting] AUTO ON — night ({temp}C)")
    else:
        if lighting.relay_state:
            lighting.lights_off()
            lighting.led_off()
            print(f"[Lighting] AUTO OFF — day ({temp}C)")

# ─── MAIN ─────────────────────────────────────────────────────────────────
def main():
    print("Booting Smart Parking System...")

    # Init hardware
    entry_sensor = Ultrasonic(trig_pin=ENTRY_TRIG, echo_pin=ENTRY_ECHO, name="Entry")
    exit_sensor  = Ultrasonic(trig_pin=EXIT_TRIG,  echo_pin=EXIT_ECHO,  name="Exit")
    entry_gate   = Gate(signal_pin=ENTRY_SERVO, name="Entry Gate")
    exit_gate    = Gate(signal_pin=EXIT_SERVO,  name="Exit Gate")
    tm           = SlotDisplay(clk_pin=TM_CLK, dio_pin=TM_DIO, ir_pins=IR_PINS)
    lcd          = ParkingLCD(sda_pin=LCD_SDA, scl_pin=LCD_SCL, address=LCD_ADDR)
    dht          = TemperatureSensor(data_pin=DHT_PIN)
    lighting     = Lighting(led_pin=LED_PIN)

    # WiFi
    ip = connect_wifi()
    telegram_flush_old_updates()

    # Web server
    server_socket = web_start()
    if ip:
        print(f"Web: http://{ip}")
        lcd.show_message(" Dashboard at:", f" {ip}")
        time.sleep(2)

    # Timing
    last_telegram    = time.ticks_ms()
    last_blynk       = time.ticks_ms()
    last_blynk_check = time.ticks_ms()  # ← add this
    last_dht         = time.ticks_ms()
    last_lcd         = time.ticks_ms()
    last_was_full    = False
    last_entry_notify = 0
    last_exit_notify  = 0
    temp_cache       = 30
    hum_cache        = 0
    last_web_request = 0

    lcd.show_welcome()
    print("System ready!\n")

    while True:
        gc.collect()
        now = time.ticks_ms()

        # 1. Ultrasonic sensors
        entry_dist, exit_dist = read_both_sensors(entry_sensor, exit_sensor)
        entry_detected = (entry_dist is not None) and (MIN_CM <= entry_dist <= MAX_CM)
        exit_detected  = (exit_dist  is not None) and (MIN_CM <= exit_dist  <= MAX_CM)
        
        # 2. Entry gate auto open
        if entry_detected and not entry_gate.is_open:
            if tm.is_full():
                lcd.show_full()
                # Only notify once every 10 seconds
                if time.ticks_diff(now, last_entry_notify) >= 10000:
                    telegram_send("Vehicle at entry — parking FULL!")
                    last_entry_notify = now
            else:
                print(">>> Vehicle at ENTRY")
                lcd.show_vehicle_entering()
                entry_gate.open_with_auto_close(GATE_DELAY)
                lighting.led_blink(times=2)
                # Only notify once per gate open event
                if time.ticks_diff(now, last_entry_notify) >= 10000:
                    telegram_send("Vehicle at entry — gate opening!")
                    last_entry_notify = now

        # 3. Exit gate auto open
        if exit_detected and not exit_gate.is_open:
            print(">>> Vehicle at EXIT")
            lcd.show_vehicle_exiting()
            exit_gate.open_with_auto_close(GATE_DELAY)
            if time.ticks_diff(now, last_exit_notify) >= 10000:
                telegram_send("Vehicle at exit — gate opening!")
                last_exit_notify = now
        
        # 4. Gate auto-close tick
        entry_gate.tick()
        exit_gate.tick()

        # 5. TM1637 update
        available = tm.update()
        total     = tm.num_slots

        # 6. Full/free alerts
        is_full_now = tm.is_full()
        if is_full_now and not last_was_full:
            telegram_send("Parking is now FULL!")
            lcd.show_full()
        elif not is_full_now and last_was_full:
            telegram_send(f"Slot freed — {available} slot(s) available.")
        last_was_full = is_full_now

        # 7. DHT11 every 3 seconds
        if time.ticks_diff(now, last_dht) >= 3000:
            t, h = dht.read()
            if t is not None: temp_cache = t
            if h is not None: hum_cache  = h
            smart_lighting(lighting, temp_cache)
            last_dht = now

        # 8. LCD every 2 seconds when idle
        if time.ticks_diff(now, last_lcd) >= 2000:
            if not entry_gate.is_open and not exit_gate.is_open and not is_full_now:
                lcd.show_status(available, total,
                                entry_gate.get_status(), exit_gate.get_status())
            last_lcd = now

        # 9. Telegram every 8 seconds
        if time.ticks_diff(now, last_telegram) >= 8000:
            # Skip Telegram if web request happened in last 3 seconds
            if time.ticks_diff(now, last_web_request) > 3000:
                check_wifi()
                telegram_process(entry_gate, exit_gate, tm, dht, lighting, lcd,
                                 gate_delay=GATE_DELAY, night_temp=NIGHT_TEMP)
            last_telegram = now

        # 10. Blynk button check every 5 seconds
        if time.ticks_diff(now, last_blynk_check) >= 5000:
            blynk_check_buttons(entry_gate, exit_gate, lighting, lcd,
                                gate_delay=GATE_DELAY)
            gc.collect()
            last_blynk_check = now

        # 11. Blynk full update every 30 seconds
        if time.ticks_diff(now, last_blynk) >= 30000:
            blynk_update(tm, dht, entry_gate, exit_gate, lighting)
            gc.collect()
            last_blynk = now

        # 12. Web server — every loop, non-blocking
        web_active = web_serve(server_socket, entry_gate, exit_gate,
                               tm, dht, lighting, lcd, gate_delay=GATE_DELAY)
        if web_active:
            last_web_request = now

        time.sleep_ms(100)
main()
