import network
import socket
import time
from machine import Pin, SoftI2C, time_pulse_us
import dht
from machine_i2c_lcd import I2cLcd

#LED SETUP
led = Pin(2, Pin.OUT)
led.off()
led_state = False

#DHT11 SETUP
dht_sensor = dht.DHT11(Pin(4))
temperature = 0.0
humidity = 0.0
last_dht_read = 0
DHT_INTERVAL = 2

# TASK 2: ULTRASONIC SETUP
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

# TASK 3: LCD SETUP
I2C_ADDR = 0x27
i2c = SoftI2C(sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
lcd.clear()

# Independent toggles
show_dist = False   # LCD line 1
show_temp = False   # LCD line 2

INTERVAL = 2
last_update = 0

# WIFI SETUP
ssid = "Robotic WIFI"
password = "rbtWIFI@2025"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)

print("Connecting to WiFi...")
while not wifi.isconnected():
    time.sleep(1)

ip = wifi.ifconfig()[0]
print("Connected! IP:", ip)

# WEB SERVER SETUP
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
s.settimeout(0.1)

print("Web server running...")

# HTML PAGE
def web_page():
    led_color = "green" if led_state else "red"
    led_text = "ON" if led_state else "OFF"

    dist_text = "{:.2f} cm".format(distance) if distance is not None else "Out of range"

    dist_btn_class = "btn-on" if show_dist else "btn-off"
    temp_btn_class = "btn-on" if show_temp else "btn-off"

    dist_btn_text = "ON" if show_dist else "OFF"
    temp_btn_text = "ON" if show_temp else "OFF"

    return f"""
    <html>
    <head>
        <title>Web Server Control</title>
        <meta http-equiv="refresh" content="2">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial;
                background: #f4f4f4;
                margin: 0;
            }}
            h1 {{
                background: #485492;
                color: white;
                padding: 15px;
                text-align: center;
                margin: 0;
            }}
            .container {{
                padding: 15px;
                max-width: 520px;
                margin: auto;
            }}
            .card {{
                background: white;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 18px;
                border: 1px solid #e5e5e5;
            }}
            .title {{
                font-weight: bold;
                margin-bottom: 10px;
                color: #2F4D6A;
            }}
            .circle {{
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: {led_color};
                margin: 10px auto;
            }}
            .row {{
                display: flex;
                justify-content: space-between;
                padding: 6px 0;
            }}
            .value {{
                color: #E39E2E;
                font-weight: bold;
            }}
            .btn {{
                width: 200px;
                height: 40px;
                font-size: 14px;
                margin: 6px;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                color: white;
            }}
            .btn-on {{
                background: #2ecc71;
            }}
            .btn-off {{
                background: #e74c3c;
            }}
            footer {{
                text-align: center;
                font-size: 12px;
                color: #555;
            }}
        </style>
    </head>

    <body>
        <h1>ESP32 Web Dashboard</h1>

        <div class="container">

            <!-- TASK 1 -->
            <div class="card">
                <div class="title">LED Control</div>
                <div class="circle"></div>
                <p style="text-align:center;">
                    LED is <span class="value">{led_text}</span>
                </p>
                <p style="text-align:center;">
                    <a href="/on"><button class="btn btn-on">ON</button></a>
                    <a href="/off"><button class="btn btn-off">OFF</button></a>
                </p>
            </div>

            <!-- TASK 2 -->
            <div class="card">
                <div class="title">DHT11 Sensor</div>
                <div class="row"><span>Temperature</span><span class="value">{temperature:.2f} C</span></div>
                <div class="row"><span>Humidity</span><span class="value">{humidity:.2f} %</span></div>
            </div>

            <div class="card">
                <div class="title">Ultrasonic Sensor</div>
                <div class="row"><span>Distance</span><span class="value">{dist_text}</span></div>
            </div>

            <!-- TASK 3 -->
            <div class="card">
                <div class="title">LCD Control</div>
                <p style="text-align:center;">
                    <a href="/toggle/dist">
                        <button class="btn {dist_btn_class}">
                            Distance LCD: {dist_btn_text}
                        </button>
                    </a><br>
                    <a href="/toggle/temp">
                        <button class="btn {temp_btn_class}">
                            Temp LCD: {temp_btn_text}
                        </button>
                    </a>
                </p>
            </div>

            <footer>
                Auto refresh every 2 seconds<br>
                ESP32 IP: {ip}
            </footer>

        </div>
    </body>
    </html>
    """

# HELPERS
def send_html(conn, html):
    conn.send("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
    conn.sendall(html)

def redirect_home(conn):
    conn.send("HTTP/1.1 302 Found\r\nLocation: /\r\nConnection: close\r\n\r\n")

# MAIN LOOP
while True:
    now = time.time()

    # ---- HANDLE HTTP REQUEST ----
    try:
        conn, addr = s.accept()
        request = conn.recv(1024).decode()

        first_line = request.split("\r\n")[0]
        path = first_line.split(" ")[1] if len(first_line.split(" ")) >= 2 else "/"

        if path == "/on":
            led.on()
            led_state = True
            redirect_home(conn)

        elif path == "/off":
            led.off()
            led_state = False
            redirect_home(conn)

        elif path == "/toggle/dist":
            show_dist = not show_dist
            if not show_dist:
                lcd.move_to(0, 0)
                lcd.putstr(" " * 16)
            redirect_home(conn)

        elif path == "/toggle/temp":
            show_temp = not show_temp
            if not show_temp:
                lcd.move_to(0, 1)
                lcd.putstr(" " * 16)
            redirect_home(conn)

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

        if show_dist:
            lcd.move_to(0, 0)
            lcd.putstr(" " * 16)
            lcd.move_to(0, 0)
            lcd.putstr(
                "Dist:{:.1f}cm".format(distance)
                if distance is not None
                else "Dist: OutOfRange"
            )

        if show_temp:
            lcd.move_to(0, 1)
            lcd.putstr(" " * 16)
            lcd.move_to(0, 1)
            lcd.putstr("Temp:{:.1f}C".format(temperature))

        last_update = now

