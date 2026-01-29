import socket
import network
import time
from machine import Pin, time_pulse_us
import dht

# LED SETUP
led = Pin(2, Pin.OUT)
led.off()
led_state = False

# DHT11 SETUP
dht_sensor = dht.DHT11(Pin(4))
temperature = 0.0
humidity = 0.0
last_dht_read = 0
DHT_INTERVAL = 2   

# ULTRASONIC SETUP
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

distance = 0.0

# WIFI SETUP
ssid = "Robotic WIFI"
password = "rbtWIFI@2025"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)

print("Connecting to WiFi...")
while not wifi.isconnected():
    time.sleep(1)

print("Connected!")
print("ESP32 IP:", wifi.ifconfig()[0])

# WEB SERVER SETUP
addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)

print("Web server running...")

# HTML PAGE
def web_page(state, temp, hum, dist):
    color = "green" if state else "red"
    status = "LED is ON" if state else "LED is OFF"
    dist_text = "{:.2f} cm".format(dist) if dist is not None else "Out of range"

    return f"""
    <html>
    <head>
        <title>ESP32 Sensor Dashboard</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body {{ font-family: Arial; text-align: center; }}
            .circle {{
                width: 80px;
                height: 80px;
                background-color: {color};
                border-radius: 50%;
                margin: 20px auto;
            }}
            button {{
                width: 140px;
                height: 45px;
                font-size: 18px;
            }}
        </style>
    </head>
    <body>
        <h1>ESP32 Web Dashboard</h1>

        <div class="circle"></div>
        <h2>{status}</h2>

        <p><a href="/on"><button>LED ON</button></a></p>
        <p><a href="/off"><button>LED OFF</button></a></p>

        <hr>

        <h2>DHT11</h2>
        <p>Temperature: <b>{temp:.2f} degree Celsius </b></p>
        <p>Humidity: <b>{hum:.2f} %</b></p>

        <hr>

        <h2>Ultrasonic</h2>
        <p>Distance: <b>{dist_text}</b></p>

        <p><small>Auto refresh every 2 seconds</small></p>
    </body>
    </html>
    """

# MAIN LOOP
while True:
    conn, addr = s.accept()
    request = conn.recv(1024).decode()

    # LED control
    if "/on" in request:
        led.on()
        led_state = True

    elif "/off" in request:
        led.off()
        led_state = False

    #DHT22 TIMED READ
    now = time.time()
    if now - last_dht_read >= DHT_INTERVAL:
        try:
            dht_sensor.measure()
            temperature = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
            last_dht_read = now
        except:
            pass

    #ULTRASONIC READ
    distance = get_distance_cm()

    # Send page
    response = web_page(led_state, temperature, humidity, distance)

    conn.send("HTTP/1.1 200 OK\r\n")
    conn.send("Content-Type: text/html\r\n")
    conn.send("Connection: close\r\n\r\n")
    conn.sendall(response)
    conn.close()