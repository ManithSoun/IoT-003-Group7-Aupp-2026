import network
import socket
import time
from machine import Pin, SoftI2C, time_pulse_us
import dht
from machine_i2c_lcd import I2cLcd

# TASK LED
led = Pin(2, Pin.OUT)
led.off()
led_state = False

# TASK DHT11
dht_sensor = dht.DHT11(Pin(4))
temperature = 0.0
humidity = 0.0
last_dht = 0
DHT_INTERVAL = 2

# TASK ULTRASONIC
TRIG = Pin(27, Pin.OUT)
ECHO = Pin(26, Pin.IN)

def get_distance_cm():
    TRIG.value(0)
    time.sleep_us(2)
    TRIG.value(1)
    time.sleep_us(10)
    TRIG.value(0)
    duration = time_pulse_us(ECHO, 1, 30000)
    if duration < 0:
        return None
    return (duration * 0.0343) / 2

distance = None

# TASK LCD
i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, 0x27, 2, 16)
lcd.clear()

show_dist = False
show_temp = False

custom_text = ""
show_text = False
scroll_index = 0

INTERVAL = 2
last_update = 0
SCROLL_DELAY = 0.25   # seconds (smooth)
last_scroll = 0

# WIFI
ssid = "Roasters home"
password = "matcha520"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)
while not wifi.isconnected():
    time.sleep(1)

ip = wifi.ifconfig()[0]

# WEB SERVER
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
s.settimeout(0.1)

# HTML PAGE
def web_page():
    dist_text = "{:.2f} cm".format(distance) if distance else "Out of range"

    return f"""
    <html>
    <head>
        <title>ESP32 Dashboard</title>
        <style>
            body {{ font-family: Arial; background:#f4f4f4; margin:0; }}
            h1 {{ background:#485492; color:white; padding:15px; text-align:center; }}
            .container {{ max-width:700px; margin:auto; padding:15px; }}

            .sensor-card {{
                background:white;
                border-radius:12px;
                padding:16px;
                margin-bottom:18px;
                border:1px solid #e5e5e5;
            }}

            .sensor-title {{
                font-weight:bold;
                color:#2F4D6A;
                margin-bottom:10px;
                text-align:center;
            }}

            .row {{
                display:flex;
                justify-content:space-between;
                padding:6px 0;
            }}

            .value {{
                color:#E39E2E;
                font-weight:bold;
            }}

            .task2-row {{
                display:flex;
                gap:15px;
            }}

            .task2-row .sensor-card {{
                flex:1;
            }}

            .btn {{
                width:200px;
                height:40px;
                border:none;
                border-radius:6px;
                color:white;
                font-size:14px;
                cursor:pointer;
            }}

            .on {{ background:#2ecc71; }}
            .off {{ background:#e74c3c; }}

            .btn-group {{
                display:flex;
                justify-content:center;
                gap:12px;
                flex-wrap:wrap;
                margin-top:10px;
            }}

            input {{
                width:90%;
                height:36px;
                margin-top:6px;
            }}

            footer {{
                text-align:center;
                font-size:12px;
                color:#555;
            }}

            @media(max-width:600px) {{
                .task2-row {{ flex-direction:column; }}
            }}
        </style>
    </head>

    <body>
        <h1>ESP32 Web Dashboard</h1>
        <div class="container">

            <!-- TASK 1 -->
            <div class="sensor-card">
                <div class="sensor-title">LED Control</div>
                <div class="btn-group">
                    <a href="/on"><button class="btn on">ON</button></a>
                    <a href="/off"><button class="btn off">OFF</button></a>
                </div>
            </div>

            <!-- TASK 2 -->
            <div class="task2-row">
                <div class="sensor-card">
                    <div class="sensor-title">DHT11 Sensor</div>
                    <div class="row"><span>Temperature</span><span class="value">{temperature:.1f} C</span></div>
                    <div class="row"><span>Humidity</span><span class="value">{humidity:.1f} %</span></div>
                </div>

                <div class="sensor-card">
                    <div class="sensor-title">Ultrasonic Sensor</div>
                    <div class="row"><span>Distance</span><span class="value">{dist_text}</span></div>
                </div>
            </div>

            <!-- TASK 3 -->
            <div class="sensor-card">
                <div class="sensor-title">LCD Control</div>
                <div class="btn-group">
                    <a href="/toggle/dist">
                        <button class="btn {'on' if show_dist else 'off'}">Distance LCD</button>
                    </a>
                    <a href="/toggle/temp">
                        <button class="btn {'on' if show_temp else 'off'}">Temp LCD</button>
                    </a>
                </div>
            </div>

            <!-- TASK 4 -->
            <div class="sensor-card">
                <div class="sensor-title">Textbox on LCD</div>
                <form action="/text" style="text-align:center;">
                    <input name="msg" placeholder="Type text for LCD">
                    <div class="btn-group">
                        <button class="btn on">Send</button>
                        <a href="/text/clear">
                            <button type="button" class="btn off">Clear Text</button>
                        </a>
                    </div>
                </form>
            </div>

            <footer>
                ESP32 IP: {ip}
            </footer>

        </div>
    </body>
    </html>
    """

# HELPERS
def send_html(conn, html):
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
    conn.sendall(html)

def redirect(conn):
    conn.send("HTTP/1.1 302 Found\r\nLocation: /\r\n\r\n")


# MAIN LOOP
while True:
    now = time.time()

    try:
        conn, addr = s.accept()
        req = conn.recv(1024).decode()
        path = req.split(" ")[1]

        if path == "/on":
            led.on()
            led_state = True
            redirect(conn)

        elif path == "/off":
            led.off()
            led_state = False
            redirect(conn)

        elif path == "/toggle/dist":
            show_dist = not show_dist
            redirect(conn)


        elif path == "/toggle/temp":
            show_temp = not show_temp
            redirect(conn)


        elif path.startswith("/text?"):
            try:
                query = path.split("?", 1)[1]
                key, value = query.split("=", 1)
                if key == "msg":
                    custom_text = value.replace("+", " ")
                    show_text = True
                    scroll_index = 0
            except:
                pass
            redirect(conn)

        elif path == "/text/clear":
            show_text = False
            custom_text = ""
            lcd.move_to(0, 0)
            lcd.putstr(" " * 16)
            redirect(conn)

        else:
            send_html(conn, web_page())

        conn.close()
    except:
        pass

    if now - last_update >= INTERVAL:
        try:
            dht_sensor.measure()
            temperature = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
        except:
            pass

        distance = get_distance_cm()

        # LCD line 1
        if show_text and custom_text:
            if now - last_scroll >= SCROLL_DELAY:
                scroll_text = custom_text + " " * 16
                lcd.move_to(0, 0)
                lcd.putstr(scroll_text[scroll_index:scroll_index + 16])
                scroll_index = (scroll_index + 1) % len(scroll_text)
                last_scroll = now

        elif show_dist:
            lcd.move_to(0, 0)
            lcd.putstr("Dist:{:.1f}cm".format(distance) if distance else "Dist: --")
        else:
            lcd.move_to(0, 0)
            lcd.putstr(" " * 16)

        # LCD line 2
        if show_temp:
            lcd.move_to(0, 1)
            lcd.putstr("Temp:{:.1f}C".format(temperature))
        else:
            lcd.move_to(0, 1)
            lcd.putstr(" " * 16)

        last_update = now
