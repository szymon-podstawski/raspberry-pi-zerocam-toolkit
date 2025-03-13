from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
import cv2
import time
import threading
import datetime
import Adafruit_DHT
import json
import os
from collections import deque
import plotly.express as px
import pandas as pd
import plotly.utils
from datetime import datetime
import argparse
import smbus2 as smbus

app = Flask(__name__)

# Konfiguracja kamery
picam2 = Picamera2()
still_config = picam2.create_still_configuration(main={"size": (2304, 1296)})
preview_config = picam2.create_preview_configuration(main={"size": (800, 600)})
camera_lock = threading.Lock()

# Zmienne globalne
measurements = deque(maxlen=100)  # Przechowuje ostatnie 100 pomiarów
output_folder = "timelapse_nowy"
interval = 60
is_running = True
photo_counter = 0

# Klasa obsługi wyświetlacza LCD
class LCD:
    def __init__(self, addr=0x27):
        self.addr = addr
        self.bus = smbus.SMBus(1)
        self.backlight = True
        self.LCD_BACKLIGHT = 0x08
        self.LCD_CMD = 0x00
        self.LCD_CHR = 0x01
        self.LCD_ENABLE = 0x04

    def write_byte(self, val):
        if self.backlight:
            val = val | self.LCD_BACKLIGHT
        self.bus.write_byte(self.addr, val)

    def strobe(self, data):
        self.write_byte(data | self.LCD_ENABLE)
        time.sleep(0.0005)
        self.write_byte(data & ~self.LCD_ENABLE)
        time.sleep(0.0005)

    def write_cmd(self, cmd):
        self.strobe(self.LCD_CMD | (cmd & 0xF0))
        self.strobe(self.LCD_CMD | ((cmd << 4) & 0xF0))

    def write_char(self, charvalue):
        self.strobe(self.LCD_CHR | (charvalue & 0xF0))
        self.strobe(self.LCD_CHR | ((charvalue << 4) & 0xF0))

    def init(self):
        time.sleep(0.020)
        self.write_byte(0x30)
        time.sleep(0.005)
        self.write_byte(0x30)
        time.sleep(0.001)
        self.write_byte(0x30)
        time.sleep(0.001)
        self.write_byte(0x20)
        time.sleep(0.001)
        self.write_cmd(0x28)
        self.write_cmd(0x08)
        self.write_cmd(0x01)
        self.write_cmd(0x06)
        self.write_cmd(0x0C)
        time.sleep(0.005)

    def clear(self):
        self.write_cmd(0x01)
        time.sleep(0.002)

    def write_string(self, message, line=0):
        if line == 0:
            self.write_cmd(0x80)
        if line == 1:
            self.write_cmd(0xC0)
        message = str(message).ljust(16)[:16]
        for i in range(len(message)):
            self.write_char(ord(message[i]))

def get_filename():
    global photo_counter
    photo_counter += 1
    return f"img_{photo_counter:03d}.jpg"

def get_dht11_data():
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)
    if humidity is not None and temperature is not None:
        return temperature, humidity
    return 0, 0

def get_timelapse_info():
    try:
        files = os.listdir(output_folder)
        return len([f for f in files if f.endswith('.jpg')])
    except:
        return 0

def capture_timelapse(output_dir, interval):
    global picam2
    while True:
        try:
            with camera_lock:
                picam2.stop()
                picam2.configure(still_config)
                picam2.start()
                filename = f"{output_dir}/{get_filename()}"
                picam2.capture_file(filename)
                print(f"Captured: {filename}")
            time.sleep(interval)
        except Exception as e:
            print(f"Error in timelapse capture: {e}")

def update_measurements():
    while True:
        temp, hum = get_dht11_data()
        measurements.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'temperature': temp,
            'humidity': hum
        })
        time.sleep(2)

def update_lcd_display():
    lcd = LCD()
    lcd.init()
    display_mode = 0
    
    while True:
        try:
            temp, hum = get_dht11_data()
            photos = get_timelapse_info()
            current_time = datetime.now().strftime('%H:%M:%S')
            
            lcd.clear()
            if display_mode == 0:
                # Temperatura i wilgotność
                lcd.write_string(f"Temp: {temp:.1f}C")
                lcd.write_string(f"Wilg: {hum:.1f}%", 1)
            elif display_mode == 1:
                # Liczba zdjęć i czas
                lcd.write_string(f"Zdjec: {photos}")
                lcd.write_string(current_time, 1)
            
            # Zmiana trybu wyświetlania
            display_mode = (display_mode + 1) % 2
            time.sleep(3)  # Zmiana co 3 sekundy
            
        except Exception as e:
            print(f"LCD Error: {e}")
            time.sleep(1)

def generate_preview():
    global picam2
    while True:
        try:
            with camera_lock:
                picam2.stop()
                picam2.configure(preview_config)
                picam2.start()
                im = picam2.capture_array()
                frame = cv2.imencode('.jpg', im)[1].tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
        except Exception as e:
            print(f"Error in preview generation: {e}")

# Szablon HTML z wykresami i podglądem
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Raspberry Pi Monitor</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background-color: #f0f0f0;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .camera-view {
            text-align: center;
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-box {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .graph {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        img {
            max-width: 100%;
            border-radius: 5px;
        }
        h1, h2 { color: #333; }
        .value { 
            font-size: 24px; 
            font-weight: bold;
            color: #2196F3;
        }
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
        function updateData() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('temp').innerText = data.temperature.toFixed(1) + '°C';
                    document.getElementById('hum').innerText = data.humidity.toFixed(1) + '%';
                    document.getElementById('photos').innerText = data.photo_count;
                    document.getElementById('time').innerText = data.current_time;
                });
        }

        function updateGraphs() {
            fetch('/graph-data')
                .then(response => response.json())
                .then(data => {
                    Plotly.newPlot('temp-graph', data.temp_graph);
                    Plotly.newPlot('hum-graph', data.hum_graph);
                });
        }

        // Aktualizuj dane co sekundę
        setInterval(updateData, 1000);
        // Aktualizuj wykresy co 10 sekund
        setInterval(updateGraphs, 10000);
    </script>
</head>
<body>
    <div class="container">
        <h1>Raspberry Pi Monitor</h1>
        
        <div class="camera-view">
            <h2>Podgląd Kamery</h2>
            <img src="{{ url_for('video_feed') }}" />
        </div>

        <div class="stats">
            <div class="stat-box">
                <h2>Temperatura</h2>
                <div class="value" id="temp">--.-°C</div>
            </div>
            <div class="stat-box">
                <h2>Wilgotność</h2>
                <div class="value" id="hum">--.-%</div>
            </div>
            <div class="stat-box">
                <h2>Liczba Zdjęć</h2>
                <div class="value" id="photos">---</div>
            </div>
            <div class="stat-box">
                <h2>Czas</h2>
                <div class="value" id="time">--:--:--</div>
            </div>
        </div>

        <div class="graph">
            <h2>Wykres Temperatury</h2>
            <div id="temp-graph"></div>
        </div>

        <div class="graph">
            <h2>Wykres Wilgotności</h2>
            <div id="hum-graph"></div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_preview(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/data')
def data():
    temp, hum = get_dht11_data()
    return json.dumps({
        'temperature': temp,
        'humidity': hum,
        'photo_count': get_timelapse_info(),
        'current_time': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/graph-data')
def graph_data():
    df = pd.DataFrame(list(measurements))
    
    if len(df) > 0:
        temp_fig = px.line(df, x='timestamp', y='temperature', title='Temperatura')
        hum_fig = px.line(df, x='timestamp', y='humidity', title='Wilgotność')
        
        return json.dumps({
            'temp_graph': temp_fig.to_dict(),
            'hum_graph': hum_fig.to_dict()
        })
    return json.dumps({})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', help='Output folder for photos', default='timelapse_nowy')
    parser.add_argument('-i', '--interval', type=int, help='Interval between photos (seconds)', default=60)
    args = parser.parse_args()

    output_folder = args.output
    interval = args.interval

    # Create folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Start timelapse thread
    timelapse_thread = threading.Thread(target=lambda: capture_timelapse(output_folder, interval))
    timelapse_thread.daemon = True
    timelapse_thread.start()

    # Start measurement thread
    measurement_thread = threading.Thread(target=update_measurements, daemon=True)
    measurement_thread.start()
    
    # Start LCD thread
    lcd_thread = threading.Thread(target=update_lcd_display, daemon=True)
    lcd_thread.start()
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, threaded=True)