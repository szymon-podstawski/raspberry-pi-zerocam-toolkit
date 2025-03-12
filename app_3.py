from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from flask import Flask, Response, render_template_string
import time
import datetime
import threading
import argparse
import os
import cv2
import logging

# Configure logging to suppress debug messages
logging.basicConfig(level=logging.WARNING)
os.environ["LIBCAMERA_LOG_LEVELS"] = "3"  # Only show warnings and errors

app = Flask(__name__)
# Disable Flask's default logging
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True

picam2 = Picamera2()

# Configuration for timelapse (high quality photos)
still_config = picam2.create_still_configuration(main={"size": (2304, 1296)})

# Configuration for preview (lower resolution for smoothness)
preview_config = picam2.create_preview_configuration(main={"size": (800, 600)})

# Global variables
output_folder = "timelapse"
interval = 60
is_running = True
camera_lock = threading.Lock()
photo_counter = 0  # Add counter for photos

def get_filename():
    global photo_counter
    photo_counter += 1
    return f"img_{photo_counter:03d}.jpg"  # Format: img_001.jpg, img_002.jpg, etc.

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
            time.sleep(0.1)  # Small delay to prevent too frequent configuration changes
        except Exception as e:
            print(f"Error in preview generation: {e}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Raspberry Pi - Camera</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; text-align: center; }
        img { max-width: 800px; margin: 20px auto; }
        .info { margin: 20px; padding: 10px; background-color: #f0f0f0; }
    </style>
</head>
<body>
    <h1>Raspberry Pi - Camera Preview</h1>
    <div class="info">
        <p>Save folder: {{output_folder}}</p>
        <p>Timelapse interval: {{interval}} seconds</p>
    </div>
    <img src="{{ url_for('video_feed') }}" />
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
        output_folder=output_folder, 
        interval=interval)

@app.route('/video_feed')
def video_feed():
    return Response(generate_preview(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', help='Output folder for photos', default='timelapse')
    parser.add_argument('-i', '--interval', type=int, help='Interval between photos (seconds)', default=60)
    args = parser.parse_args()

    output_folder = args.output
    interval = args.interval

    # Create folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Start timelapse in separate thread
    timelapse_thread = threading.Thread(target=lambda: capture_timelapse(output_folder, interval))
    timelapse_thread.daemon = True
    timelapse_thread.start()

    # Run Flask server
    app.run(host='0.0.0.0', port=5000) 