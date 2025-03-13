from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
import cv2
import time
import threading
import datetime
import Adafruit_DHT
import json
import os
import argparse
from collections import deque
import plotly.express as px
import pandas as pd
import plotly.utils
from datetime import datetime
from smbus2 import SMBus

# Parsowanie argumentów
parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output', default='timelapse_nowy', help='Folder na zdjęcia timelapsu')
parser.add_argument('-i', '--interval', type=int, default=60, help='Interwał między zdjęciami (sekundy)')
args = parser.parse_args()

app = Flask(__name__)

# Konfiguracja kamery
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(main={"size": (800, 600)})
still_config = picam2.create_still_configuration(main={"size": (2304, 1296)})
camera_lock = threading.Lock()

# Zmienne globalne
measurements = deque(maxlen=100)  # Przechowuje ostatnie 100 pomiarów
output_folder = args.output
interval = args.interval

# Konfiguracja LCD
LCD_ADDR = 0x27
LCD_WIDTH = 16
bus = SMBus(1)

def lcd_init():
    try:
        # Inicjalizacja wyświetlacza
        lcd_write(0x33, 0)
        lcd_write(0x32, 0)
        lcd_write(0x06, 0)
        lcd_write(0x0C, 0)
        lcd_write(0x28, 0)
        lcd_write(0x01, 0)
        time.sleep(0.05)
    except Exception as e:
        print(f"Błąd inicjalizacji LCD: {e}")

def lcd_write(data, mode):
    try:
        if mode:
            bus.write_byte(LCD_ADDR, data | 0x09)
            bus.write_byte(LCD_ADDR, data | 0x0D)
            bus.write_byte(LCD_ADDR, data | 0x09)
        else:
            bus.write_byte(LCD_ADDR, data & 0xFB)
            bus.write_byte(LCD_ADDR, (data & 0xFB) | 0x04)
            bus.write_byte(LCD_ADDR, data & 0xFB)
        time.sleep(0.002)
    except Exception as e:
        print(f"Błąd zapisu LCD: {e}")

def lcd_clear():
    lcd_write(0x01, 0)

def lcd_display_string(string, line):
    try:
        if line == 1:
            lcd_write(0x80, 0)
        if line == 2:
            lcd_write(0xC0, 0)

        for char in string:
            lcd_write(ord(char), 1)
    except Exception as e:
        print(f"Błąd wyświetlania na LCD: {e}")

def update_lcd():
    while True:
        try:
            temp, hum = get_dht11_data()
            photos = get_timelapse_info()
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Pierwsza strona - temperatura i wilgotność
            lcd_clear()
            lcd_display_string(f"Temp: {temp:.1f}C", 1)
            lcd_display_string(f"Wilg: {hum:.1f}%", 2)
            time.sleep(3)
            
            # Druga strona - liczba zdjęć i czas
            lcd_clear()
            lcd_display_string(f"Zdjec: {photos}", 1)
            lcd_display_string(f"Czas: {current_time}", 2)
            time.sleep(3)
        except Exception as e:
            print(f"Błąd aktualizacji LCD: {e}")
            time.sleep(1)

def capture_timelapse():
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    photo_counter = len([f for f in os.listdir(output_folder) if f.endswith('.jpg')])
    
    while True:
        try:
            with camera_lock:
                picam2.configure(still_config)
                picam2.start()
                time.sleep(2)  # Czas na dostosowanie ekspozycji
                
                # Zrób zdjęcie
                photo_counter += 1
                filename = os.path.join(output_folder, f'img_{photo_counter:03d}.jpg')
                picam2.capture_file(filename)
                print(f"Zapisano zdjęcie: {filename}")
                
                picam2.configure(preview_config)
                picam2.start()
        except Exception as e:
            print(f"Błąd podczas robienia zdjęcia: {e}")
        
        time.sleep(interval)

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

def update_measurements():
    while True:
        temp, hum = get_dht11_data()
        measurements.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'temperature': temp,
            'humidity': hum
        })
        time.sleep(2)

def generate_preview():
    while True:
        try:
            with camera_lock:
                picam2.configure(preview_config)
                picam2.start()
                im = picam2.capture_array()
                frame = cv2.imencode('.jpg', im)[1].tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
        except Exception as e:
            print(f"Error in preview: {e}")
            time.sleep(1)

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

        setInterval(updateData, 1000);
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

if __name__ == '__main__':
    try:
        # Utwórz folder na zdjęcia jeśli nie istnieje
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Inicjalizacja LCD
        lcd_init()
        
        # Start wątku LCD
        lcd_thread = threading.Thread(target=update_lcd, daemon=True)
        lcd_thread.start()
        
        # Start wątku pomiarów
        measurement_thread = threading.Thread(target=update_measurements, daemon=True)
        measurement_thread.start()
        
        # Start wątku timelapsu
        timelapse_thread = threading.Thread(target=capture_timelapse, daemon=True)
        timelapse_thread.start()
        
        # Start serwera Flask
        app.run(host='0.0.0.0', port=5000, threaded=True)
        
    except KeyboardInterrupt:
        print("\nZatrzymywanie aplikacji...")
    except Exception as e:
        print(f"Błąd podczas uruchamiania: {e}")
    finally:
        try:
            lcd_clear()
            bus.close()
        except:
            pass