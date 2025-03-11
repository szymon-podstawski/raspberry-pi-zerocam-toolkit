from flask import Flask, Response
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import io
import logging
import time

app = Flask(__name__)
picam2 = None

def init_camera():
    global picam2
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(main={"size": (800, 600)})
    picam2.configure(preview_config)
    picam2.start_preview()
    picam2.start()
    time.sleep(2)  # Give camera time to initialize
    logging.info("Camera initialized")

def generate_frames():
    while True:
        try:
            # Get frame as numpy array
            frame = picam2.capture_array()
            # Save as JPEG to buffer
            output = io.BytesIO()
            picam2.capture_file(output, format='jpeg')
            frame = output.getvalue()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
        except Exception as e:
            logging.error(f"Error generating frame: {str(e)}")
            time.sleep(1)

@app.route('/')
def index():
    return '''
    <html>
        <head>
            <title>Raspberry Pi Camera Preview</title>
            <style>
                body { 
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }
                h1 { color: #333; }
                img { 
                    max-width: 100%;
                    border: 2px solid #ccc;
                    border-radius: 8px;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <h1>Raspberry Pi Camera Preview</h1>
            <img src="/video_feed" />
        </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        init_camera()
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        if picam2:
            picam2.close() 