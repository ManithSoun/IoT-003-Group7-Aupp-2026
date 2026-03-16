# telegram_bot.py
import urequests
import ujson
import time
import gc

BOT_TOKEN    = "token"
ALLOWED_ID   = chat id
BOT_TOPIC_ID = 16 (change id)
BASE_URL     = f"https://api.telegram.org/bot{BOT_TOKEN}"

last_update_id = 0
_first_poll    = True

def safe_request(method, url, body=None):
    gc.collect()
    try:
        if method == "GET":
            r = urequests.get(url, timeout=8)
        else:
            r = urequests.post(url, data=body,
                               headers={"Content-Type": "application/json"},
                               timeout=8)
        data = r.text
        r.close()
        del r
        gc.collect()
        return data
    except Exception as e:
        print("[Telegram]", e)
        gc.collect()
        return None

def telegram_send(text):
    body = ujson.dumps({
        "chat_id"           : ALLOWED_ID,
        "text"              : text,
        "message_thread_id" : BOT_TOPIC_ID
    })
    result = safe_request("POST", f"{BASE_URL}/sendMessage", body)
    if result:
        print("[Telegram] Sent")

def telegram_get_updates():
    global last_update_id, _first_poll
    url  = f"{BASE_URL}/getUpdates?offset={last_update_id+1}&timeout=0"
    data = safe_request("GET", url)
    if not data:
        return []
    try:
        obj = ujson.loads(data)
    except:
        return []
    if not obj.get("ok"):
        return []
    results = obj["result"]
    if _first_poll and results:
        last_update_id = results[-1]["update_id"]
        _first_poll = False
        print(f"[Telegram] Skipped {len(results)} old messages.")
        return []
    _first_poll = False
    return results

def telegram_process(entry_gate, exit_gate, tm, dht, lighting, lcd,
                     gate_delay=5, night_temp=30,
                     emergency_mode=False, cars_entered=0, cars_exited=0):
    global last_update_id
    updates = telegram_get_updates()

    for update in updates:
        last_update_id = update["update_id"]
        if "message" not in update:
            continue

        msg       = update["message"]
        chat_id   = msg["chat"]["id"]
        text      = msg.get("text", "").lower().strip()
        thread_id = msg.get("message_thread_id")

        if "@" in text:
            text = text.split("@")[0]

        if not text.startswith("/"):
            continue

        if chat_id != ALLOWED_ID or thread_id != BOT_TOPIC_ID:
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
                f"Lights: {lighting.get_relay_status()} ({'AUTO' if lighting.auto_mode else 'MAN'})\n"
                f"Mode  : {'EMERGENCY' if emergency_mode else 'NORMAL'}"
            )
        elif text == "/slots":
            statuses = tm.get_slot_status()
            lines    = [f"Parking Slots ({available}/{total} free)"]
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
                telegram_send(f"Temp : {temp}C\nHumid: {hum}%\nMode : {mode}")
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
            telegram_send(f"Lights AUTO.\nON when temp < {night_temp}C.")
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
            percent  = int((occupied / total) * 100) if total > 0 else 0
            telegram_send(
                f"BloomLot Stats\n"
                f"Slots free   : {available}/{total}\n"
                f"Occupancy    : {percent}%\n"
                f"Cars entered : {cars_entered}\n"
                f"Cars exited  : {cars_exited}"
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

    return emergency_mode