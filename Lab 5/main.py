from machine import Pin, I2C, PWM
import neopixel
import network
import socket
import time
import tcs34725

# ── Setup ──────────────────────────────────────────────
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
sensor = tcs34725.TCS34725(i2c)
led = neopixel.NeoPixel(Pin(23), 24)

ena = PWM(Pin(14), freq=1000)
in1 = Pin(26, Pin.OUT)
in2 = Pin(27, Pin.OUT)

# ── WiFi ───────────────────────────────────────────────
ssid = "Roasters home"
password = "matcha520"

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect(ssid, password)
print("Connecting", end="")
while not wifi.isconnected():
    print(".", end="")
    time.sleep(0.5)
print("\nConnected!")
print("ESP32 IP:", wifi.ifconfig()[0])

# ── Variables ──────────────────────────────────────────
neo_r, neo_g, neo_b = 0, 0, 0
detected_color = "UNKNOWN"
manual_mode = False
manual_timer = 0

# ── Functions ──────────────────────────────────────────
def classify_color(r, g, b):
    if r > g and r > b:
        return "RED"
    elif g > r and g > b:
        return "GREEN"
    elif b > r and b > g:
        return "BLUE"
    else:
        return "UNKNOWN"

def set_neopixel(r, g, b):
    for i in range(24):
        led[i] = (r, g, b)
    led.write()

def forward(speed=700):
    in1.value(1)
    in2.value(0)
    ena.duty(speed)
    print(f"CMD: FORWARD speed={speed}")

def backward(speed=700):
    in1.value(0)
    in2.value(1)
    ena.duty(speed)
    print(f"CMD: BACKWARD speed={speed}")

def stop():
    in1.value(0)
    in2.value(0)
    ena.duty(0)
    print("CMD: STOP")

def set_manual():
    global manual_mode, manual_timer
    manual_mode = True
    manual_timer = time.time()

# ── Web Server ─────────────────────────────────────────
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(addr)
server.listen(5)
print("Server running...")
print("-" * 40)

while True:
    # ── Auto timeout after 10 seconds ──────────────────
    if manual_mode and (time.time() - manual_timer > 10):
        manual_mode = False
        print("Back to AUTO mode")

    # ── Sensor Reading ─────────────────────────────────
    r, g, b, c = sensor.read_raw()
    detected_color = classify_color(r, g, b)
    print(f"R:{r:>4} G:{g:>4} B:{b:>4} | {detected_color} | Manual:{manual_mode}")

    # ── Auto Mode ──────────────────────────────────────
    if not manual_mode:
        if detected_color == "RED":
            set_neopixel(255, 0, 0)
            in1.value(1)
            in2.value(0)
            ena.duty(700)
        elif detected_color == "GREEN":
            set_neopixel(0, 255, 0)
            in1.value(1)
            in2.value(0)
            ena.duty(500)
        elif detected_color == "BLUE":
            set_neopixel(0, 0, 255)
            in1.value(1)
            in2.value(0)
            ena.duty(300)
        else:
            set_neopixel(0, 0, 0)
            ena.duty(0)

    # ── Handle App Request ─────────────────────────────
    try:
        client, addr = server.accept()
        request = client.recv(1024).decode()
        response = "OK"

        if "GET /forward" in request:
            set_manual()
            forward()
            response = "Forward"

        elif "GET /backward" in request:
            set_manual()
            backward()
            response = "Backward"

        elif "GET /stop" in request:
            set_manual()
            stop()
            response = "Stop"

        elif "GET /motor-speed" in request:
            try:
                set_manual()
                val = int(float(request.split("value=")[1].split(" ")[0]))
                val = max(0, min(1023, val))
                in1.value(1)
                in2.value(0)
                ena.duty(val)
                response = f"MotorSpeed:{val}"
                print(f"CMD: MOTOR {val}")
            except:
                response = "Invalid"

        elif "GET /red" in request:
            try:
                set_manual()
                neo_r = int(float(request.split("value=")[1].split(" ")[0]))
                neo_r = max(0, min(255, neo_r))
                set_neopixel(neo_r, neo_g, neo_b)
                response = f"Red:{neo_r}"
                print(f"CMD: RED {neo_r}")
            except:
                response = "Invalid"

        elif "GET /green" in request:
            try:
                set_manual()
                neo_g = int(float(request.split("value=")[1].split(" ")[0]))
                neo_g = max(0, min(255, neo_g))
                set_neopixel(neo_r, neo_g, neo_b)
                response = f"Green:{neo_g}"
                print(f"CMD: GREEN {neo_g}")
            except:
                response = "Invalid"

        elif "GET /blue" in request:
            try:
                set_manual()
                neo_b = int(float(request.split("value=")[1].split(" ")[0]))
                neo_b = max(0, min(255, neo_b))
                set_neopixel(neo_r, neo_g, neo_b)
                response = f"Blue:{neo_b}"
                print(f"CMD: BLUE {neo_b}")
            except:
                response = "Invalid"

        elif "GET /auto" in request:
            manual_mode = False
            response = "AutoMode"
            print("CMD: AUTO MODE ON")

        elif "GET /color" in request:
            response = detected_color

        else:
            response = "Invalid command"

        client.send("HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n")
        client.send(response)
        client.close()

    except OSError:
        pass

    time.sleep(0.1)
