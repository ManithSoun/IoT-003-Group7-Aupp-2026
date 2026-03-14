# telegram_bot.py
import urequests
import ujson
import gc
import time
import network

BOT_TOKEN    = "8378245115:AAEwSFBK-Noxo38CT-NS8kE4p8Ht9qMkuBA"
ALLOWED_ID   = -1003859247655
BOT_TOPIC_ID = 16
BASE_URL     = f"https://api.telegram.org/bot{BOT_TOKEN}"

last_update_id = 0

def _wifi_reset():
    """Reconnect WiFi to clear stale SSL state."""
    try:
        wlan = network.WLAN(network.STA_IF)
        if not wlan.isconnected():
            wlan.connect()
            timeout = 5
            while not wlan.isconnected() and timeout > 0:
                time.sleep_ms(500)
                timeout -= 1
    except:
        pass
    gc.collect()

def telegram_send(text, retry=3):
    for attempt in range(retry):
        gc.collect()
        _wifi_reset()
        try:
            url  = f"{BASE_URL}/sendMessage"
            body = ujson.dumps({
                "chat_id"           : ALLOWED_ID,
                "text"              : text,
                "message_thread_id" : BOT_TOPIC_ID
            })
            r = urequests.post(url, data=body,
                               headers={"Content-Type": "application/json"},
                               timeout=10)
            r.close()
            gc.collect()
            print("[Telegram] Sent")
            return
        except Exception as e:
            print(f"[Telegram] Send attempt {attempt+1}: {e}")
            gc.collect()
            time.sleep_ms(1000 * (attempt + 1))
    print("[Telegram] All retries failed")

def telegram_flush_old_updates():
    global last_update_id
    gc.collect()
    _wifi_reset()
    try:
        url  = f"{BASE_URL}/getUpdates?timeout=0"
        r    = urequests.get(url, timeout=10)
        data = ujson.loads(r.text)
        r.close()
        gc.collect()
        if data.get("ok") and data["result"]:
            last_update_id = data["result"][-1]["update_id"]
            print(f"[Telegram] Flushed {len(data['result'])} old messages.")
    except Exception as e:
        print(f"[Telegram] Flush error: {e}")

def telegram_get_updates():
    global last_update_id
    gc.collect()
    _wifi_reset()
    try:
        url  = f"{BASE_URL}/getUpdates?offset={last_update_id + 1}&timeout=0"
        r    = urequests.get(url, timeout=10)
        data = ujson.loads(r.text)
        r.close()
        gc.collect()
        if data.get("ok") and data["result"]:
            return data["result"]
    except Exception as e:
        print(f"[Telegram] Poll error: {e}")
        gc.collect()
        time.sleep_ms(2000)
    return []

def telegram_process(entry_gate, exit_gate, tm, dht, lighting, lcd, gate_delay=5, night_temp=28):
    global last_update_id
    updates = telegram_get_updates()

    for update in updates:
        last_update_id = update["update_id"]
        if "message" not in update:
            continue

        chat_id   = update["message"]["chat"]["id"]
        text      = update["message"].get("text", "")
        thread_id = update["message"].get("message_thread_id", None)

        if not text:
            continue

        text = text.strip().lower()
        if "@" in text:
            text = text.split("@")[0]

        if not text.startswith("/"):
            continue

        if thread_id != BOT_TOPIC_ID:
            continue

        if chat_id != ALLOWED_ID:
            telegram_send("Unauthorised.")
            continue

        print(f"[Telegram] Command: {text}")

        available = tm.get_available_count()
        total     = tm.num_slots
        temp, hum = dht.read()

        if text == "/status":
            telegram_send(
                f"Parking Status\n"
                f"Slots : {available}/{total}\n"
                f"Entry : {entry_gate.get_status()}\n"
                f"Exit  : {exit_gate.get_status()}\n"
                f"Temp  : {temp}C  Hum:{hum}%\n"
                f"Lights: {lighting.get_relay_status()} ({'AUTO' if lighting.auto_mode else 'MAN'})"
            )

        elif text == "/slots":
            statuses = tm.get_slot_status()
            lines    = [f"Parking Slots ({available}/{total} free)"]
            for i, occ in enumerate(statuses):
                lines.append(f"  Slot {i+1}: {'Occupied' if occ else 'Empty'}")
            if tm.is_full():
                lines.append("\nParking is FULL!")
            telegram_send("\n".join(lines))
            
        elif text == "/open":
            available = tm.get_available_count()
            full = tm.is_full()
            print(f"[Telegram] /open — available:{available} full:{full}")
            if full:
                telegram_send("Parking FULL! Cannot open.")
            else:
                lcd.show_vehicle_entering()
                entry_gate.open()
                telegram_send("Entry gate open.")
                
        elif text == "/close":
            entry_gate.close()
            telegram_send("Entry gate closed.")
            
        elif text == "/open_exit":
            lcd.show_vehicle_exiting()
            exit_gate.open()
            telegram_send("Exit gate opening. Send /close_exit to close.")
            
        elif text == "/close_exit":
            exit_gate.close()
            telegram_send("Exit gate closed.")
            
        elif text == "/temp":
            if temp is None:
                telegram_send("Sensor error — check DHT11 wiring.")
            else:
                mode = "Night - lights ON" if temp < night_temp else "Day - lights OFF"
                telegram_send(f"Temp : {temp}C\nHumid: {hum}%\nMode : {mode}")
        elif text == "/light_on":
            lighting.set_auto_mode(False)
            lighting.lights_on()
            lighting.led_on()
            telegram_send("Lights ON (manual mode).")
            
        elif text == "/light_off":
            lighting.set_auto_mode(False)
            lighting.lights_off()
            lighting.led_off()
            telegram_send("Lights OFF (manual mode).")
            
        elif text == "/light_auto":
            lighting.set_auto_mode(True)
            telegram_send(f"Lights AUTO mode.\nON when temp < {night_temp}C.")
            
        elif text == "/help":
            telegram_send(
                "/status - System overview\n"
                "/slots - Slot details\n"
                "/temp - Temperature & humidity\n"
                "/open - Open entry gate\n"
                "/close - Close entry gate\n"
                "/open_exit - Open exit gate\n"
                "/close_exit - Close exit gate\n"
                "/light_on - Lights ON manual\n"
                "/light_off - Lights OFF manual\n"
                "/light_auto - Lights auto mode"
            )
        else:
            telegram_send("Unknown command. Type /help")
