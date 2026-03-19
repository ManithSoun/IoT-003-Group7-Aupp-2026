# telegram_bot.py - Detailed Responses Version
import time
import ubinascii
import machine
from umqtt.simple import MQTTClient

# MQTT Bridge Configuration
MQTT_BROKER = "192.168.18.39"
MQTT_PORT = 1883
MQTT_TOPIC_SEND = "parking/telegram/send"
MQTT_TOPIC_RECV = "parking/telegram/recv"

CLIENT_ID = ubinascii.hexlify(machine.unique_id()).decode()

# Global
mqtt_client = None
_last_full = 0
_last_cmd = 0
_last_ping = 0
_pending = None

def mqtt_connect():
    global mqtt_client
    try:
        print("[MQTT] Connecting...")
        mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.connect()
        print("[MQTT] Connected!")
        
        def cb(topic, msg):
            global _pending
            _pending = msg.decode()
            print(f"\n📨 Command: {_pending}")
        
        mqtt_client.set_callback(cb)
        mqtt_client.subscribe(MQTT_TOPIC_RECV)
        return True
    except Exception as e:
        print(f"[MQTT] Failed: {e}")
        mqtt_client = None
        return False

def telegram_send(text):
    global mqtt_client
    if not mqtt_client:
        if not mqtt_connect():
            return False
    try:
        mqtt_client.publish(MQTT_TOPIC_SEND, text)
        return True
    except:
        mqtt_client = None
        return False

def check_for_commands():
    global mqtt_client, _pending
    if not mqtt_client:
        return None
    try:
        mqtt_client.check_msg()
    except:
        mqtt_client = None
    if _pending:
        cmd = _pending
        _pending = None
        return cmd
    return None

def telegram_process(entry_gate, exit_gate, tm, dht, lighting, lcd,
                     gate_delay=5, night_temp=30,
                     emergency_mode=False, cars_entered=0, cars_exited=0):
    global _last_full, _last_cmd, _last_ping, _pending, mqtt_client
    
    now = time.time()
    available = tm.get_available_count()
    total = tm.num_slots
    temp, hum = dht.read()
    
    # Ensure connection
    if not mqtt_client:
        mqtt_connect()
    
    # Full alert
    if tm.is_full() and now - _last_full > 600:
        if telegram_send("FULL"):
            _last_full = now
    
    # Check commands
    if now - _last_cmd > 5:
        cmd = check_for_commands()
        _last_cmd = now
        
        if cmd:
            text = cmd.lower().strip()
            print(f"[Telegram] Command: {text}")
            
            if text == "/status":
                telegram_send(
                    f"Parking Status\n"
                    f"Slots : {available}/{total}\n"
                    f"Entry : {entry_gate.get_status()}\n"
                    f"Exit  : {exit_gate.get_status()}\n"
                    f"Temp  : {temp}C  Hum:{hum}%\n"
                    f"Lights: {lighting.get_relay_status()} ({'AUTO' if lighting.auto_mode else 'MAN'})\n"
                    f"Mode  : {'EMERGENCY' if emergency_mode else 'NORMAL'}"
                )
                
            elif text == "/slots":
                statuses = tm.get_slot_status()
                lines = [f"Parking Slots ({available}/{total} free)"]
                for i, occ in enumerate(statuses):
                    lines.append(f"  Slot {i+1}: {'Occupied' if occ else 'Empty'}")
                if tm.is_full():
                    lines.append("\nParking FULL!")
                telegram_send("\n".join(lines))
                
            elif text == "/open":
                if tm.is_full():
                    telegram_send("Parking FULL! Cannot open.")
                else:
                    entry_gate.open()
                    telegram_send("Entry gate open. Send /close to close.")
                    
            elif text == "/close":
                entry_gate.close()
                telegram_send("Entry gate closed.")
                
            elif text == "/open_exit":
                exit_gate.open()
                telegram_send("Exit gate open. Send /close_exit to close.")
                
            elif text == "/close_exit":
                exit_gate.close()
                telegram_send("Exit gate closed.")
                
            elif text == "/temp":
                if temp is None:
                    telegram_send("Sensor error — check DHT11.")
                else:
                    mode = "Night - lights ON" if temp < night_temp else "Day - lights OFF"
                    telegram_send(f"Temperature: {temp}C\nHumidity: {hum}%\nMode: {mode}")
                    
            elif text == "/light_on":
                lighting.set_auto_mode(False)
                lighting.lights_on()
                lighting.led_on()
                telegram_send("Lights ON (manual).")
                
            elif text == "/light_off":
                lighting.set_auto_mode(False)
                lighting.lights_off()
                lighting.led_off()
                telegram_send("Lights OFF (manual).")
                
            elif text == "/light_auto":
                lighting.set_auto_mode(True)
                telegram_send(f"Lights AUTO.\nON when temp < {night_temp}C.\nTemp now: {temp}C")
                
            elif text == "/emergency":
                emergency_mode = True
                entry_gate.open()
                exit_gate.open()
                lighting.set_auto_mode(False)
                lighting.lights_on()
                lighting.led_on()
                telegram_send(
                    "EMERGENCY MODE ACTIVATED!\n"
                    "Both gates opened.\n"
                    "Lights ON.\n"
                    "Send /reset to deactivate."
                )
                print("[EMERGENCY] Mode activated!")
                
            elif text == "/reset":
                emergency_mode = False
                entry_gate.close()
                exit_gate.close()
                lighting.set_auto_mode(True)
                telegram_send(
                    "Emergency mode deactivated.\n"
                    "Both gates closed.\n"
                    "System back to normal."
                )
                print("[EMERGENCY] Mode deactivated!")
                
            elif text == "/stats":
                occupied = total - available
                percent = int((occupied / total) * 100) if total > 0 else 0
                telegram_send(
                    f"BloomLot Daily Stats\n"
                    f"Cars entered : {cars_entered}\n"
                    f"Cars exited  : {cars_exited}\n"
                    f"Occupancy    : {percent}%\n"
                    f"Slots free   : {available}/{total}"
                )
                
            elif text == "/help":
                telegram_send(
                    "/status - System overview\n"
                    "/slots - Slot details\n"
                    "/temp - Temperature & humidity\n"
                    "/stats - Daily summary\n"
                    "/open - Open entry gate\n"
                    "/close - Close entry gate\n"
                    "/open_exit - Open exit gate\n"
                    "/close_exit - Close exit gate\n"
                    "/light_on - Lights ON manual\n"
                    "/light_off - Lights OFF manual\n"
                    "/light_auto - Lights auto mode\n"
                    "/emergency - Emergency mode\n"
                    "/reset - Deactivate emergency"
                )
                
            else:
                telegram_send("Unknown command. Type /help")
    
    # Ping every 30s
    if mqtt_client and now - _last_ping > 30:
        try:
            mqtt_client.ping()
            _last_ping = now
        except:
            mqtt_client = None
    
    return emergency_mode
