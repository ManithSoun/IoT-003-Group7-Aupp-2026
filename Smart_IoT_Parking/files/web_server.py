# web_server.py
import usocket

NIGHT_TEMP = 30

def build_html(available, total, temp, hum, entry_status, exit_status, light_status, auto_mode):
    return (
        "<!DOCTYPE html><html><head>"
        "<title>Parking</title>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta http-equiv='refresh' content='5'>"
        "<style>"
        "body{font-family:Arial;background:#111;color:#eee;text-align:center;padding:10px}"
        "h1{color:#00d4ff;font-size:20px}"
        ".c{background:#222;border-radius:8px;padding:12px;margin:8px auto;max-width:360px}"
        ".g{color:#00ff88}.r{color:#ff4444}.y{color:#ffcc00}"
        ".big{font-size:40px;font-weight:bold}"
        "a button{background:#00d4ff;border:none;padding:8px 14px;border-radius:6px;"
        "color:#000;font-size:13px;margin:3px;font-weight:bold}"
        ".off{background:#ff4444;color:#fff}"
        ".au{background:#00ff88;color:#000}"
        "</style></head><body>"
        "<h1>Smart Parking</h1>"
        "<div class='c'>"
        "<div class='big " + ("g" if available > 0 else "r") + "'>" + str(available) + "/" + str(total) + "</div>"
        "<p>" + ("Available" if available > 0 else "FULL") + "</p></div>"
        "<div class='c'><b>Entry Gate</b> <span class='" + ("g" if entry_status=="OPEN" else "y") + "'>" + entry_status + "</span><br><br>"
        "<a href='/open_entry'><button>Open</button></a>"
        "<a href='/close_entry'><button class='off'>Close</button></a></div>"
        "<div class='c'><b>Exit Gate</b> <span class='" + ("g" if exit_status=="OPEN" else "y") + "'>" + exit_status + "</span><br><br>"
        "<a href='/open_exit'><button>Open</button></a>"
        "<a href='/close_exit'><button class='off'>Close</button></a></div>"
        "<div class='c'><b>Temp:</b> " + str(temp) + "C &nbsp; <b>Hum:</b> " + str(hum) + "%</div>"
        "<div class='c'><b>Lights:</b> <span class='" + ("g" if light_status=="ON" else "y") + "'>" + light_status + "</span>"
        " <span class='y'>(" + ("AUTO" if auto_mode else "MANUAL") + ")</span><br><br>"
        "<a href='/light_on'><button>ON</button></a>"
        "<a href='/light_off'><button class='off'>OFF</button></a>"
        "<a href='/light_auto'><button class='au'>Auto</button></a></div>"
        "</body></html>"
    )

def web_start():
    """Create and return the server socket."""
    server_socket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
    server_socket.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
    server_socket.bind(("", 80))
    server_socket.listen(1)
    return server_socket

def web_serve(server_socket, entry_gate, exit_gate, tm, dht, lighting, lcd, gate_delay=5):
    try:
        server_socket.settimeout(0.01)
        conn, addr = server_socket.accept()
        conn.settimeout(2)
        try:
            request = conn.recv(512).decode()
            path    = request.split(" ")[1] if " " in request else "/"
        except:
            conn.close()
            return False   # ← return False = no request

        action_taken = False
        if   "/open_entry"  in path: entry_gate.open();  lcd.show_vehicle_entering(); action_taken = True
        elif "/close_entry" in path: entry_gate.close(); action_taken = True
        elif "/open_exit"   in path: exit_gate.open();   lcd.show_vehicle_exiting();  action_taken = True
        elif "/close_exit"  in path: exit_gate.close();  action_taken = True
        elif "/light_on"    in path: lighting.set_auto_mode(False); lighting.lights_on();  lighting.led_on();  action_taken = True
        elif "/light_off"   in path: lighting.set_auto_mode(False); lighting.lights_off(); lighting.led_off(); action_taken = True
        elif "/light_auto"  in path: lighting.set_auto_mode(True);  action_taken = True

        if action_taken:
            conn.send("HTTP/1.1 302 Found\r\nLocation: /\r\nConnection: close\r\n\r\n")
            conn.close()
            return True   # ← request handled

        available = tm.get_available_count()
        total     = tm.num_slots
        temp, hum = dht.read()
        html      = build_html(
            available, total, temp, hum,
            entry_gate.get_status(), exit_gate.get_status(),
            lighting.get_relay_status(), lighting.auto_mode
        )
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n" + html
        conn.send(response)
        conn.close()
        return True   # ← request handled

    except OSError:
        return False  # ← no request
