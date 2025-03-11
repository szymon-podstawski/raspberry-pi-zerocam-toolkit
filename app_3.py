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

app = Flask(__name__)
picam2 = Picamera2()

# Configuration for timelapse (high quality photos)
still_config = picam2.create_still_configuration(main={"size": (2304, 1296)})

# Configuration for preview (lower resolution for smoothness)
preview_config = picam2.create_preview_configuration(main={"size": (800, 600)})

# Global variables
output_folder = "timelapse"
interval = 60
is_running = True

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def capture_timelapse():
    global is_running
    while is_running:
        # Switch to photo configuration
        picam2.switch_mode_and_capture_file(still_config, 
            f"{output_folder}/timelapse_{get_timestamp()}.jpg")
        time.sleep(interval)

def generate_preview():
    # Switch to preview configuration
    picam2.configure(preview_config)
    picam2.start()
    
    while True:
        frame = picam2.capture_array()
        # Convert to JPEG
        success, jpeg_data = cv2.imencode('.jpg', frame)
        if success:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data.tobytes() + b'\r\n')
        time.sleep(0.1)

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
    timelapse_thread = threading.Thread(target=capture_timelapse)
    timelapse_thread.daemon = True
    timelapse_thread.start()

    # Run Flask server
    app.run(host='0.0.0.0', port=5000) 