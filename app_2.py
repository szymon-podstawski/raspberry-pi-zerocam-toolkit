from picamera2 import Picamera2
import time
from datetime import datetime
import os
import argparse
import signal
import sys
import subprocess

class TimelapseCamera:
    def __init__(self, interval=60, output_dir='timelapse'):
        self.interval = interval
        self.output_dir = output_dir
        self.running = False
        self.picam2 = None
        
        # Make sure the directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Handle stop signal
        signal.signal(signal.SIGINT, self.stop_signal_handler)
        
    def init_camera(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_still_configuration(main={"size": (2304, 1296)})
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(2)  # Give camera time to initialize
        
    def take_photo(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/timelapse_{timestamp}.jpg"
        self.picam2.capture_file(filename)
        print(f"Photo taken: {filename}")
        
    def create_video(self):
        print("\nCreating video from collected photos...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = f"timelapse_video_{timestamp}.mp4"
        
        # Check if there are any photos
        photos = sorted([f for f in os.listdir(self.output_dir) if f.endswith('.jpg')])
        if not photos:
            print("No photos found to create video!")
            return
        
        try:
            # Use ffmpeg to create video
            cmd = [
                'ffmpeg',
                '-framerate', '24',  # 24 frames per second
                '-pattern_type', 'glob',
                '-i', f'{self.output_dir}/timelapse_*.jpg',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                video_name
            ]
            subprocess.run(cmd, check=True)
            print(f"\nVideo has been created: {video_name}")
            print(f"Number of photos used: {len(photos)}")
            
        except subprocess.CalledProcessError as e:
            print(f"\nError while creating video: {e}")
        except Exception as e:
            print(f"\nUnexpected error: {e}")
        
    def start(self):
        print(f"Starting timelapse. Interval: {self.interval} seconds")
        print("Press Ctrl+C to stop")
        self.running = True
        self.init_camera()
        
        try:
            while self.running:
                self.take_photo()
                time.sleep(self.interval)
        finally:
            if self.picam2:
                self.picam2.close()
            # Create video after recording is finished
            self.create_video()
                
    def stop_signal_handler(self, signum, frame):
        print("\nStopping timelapse...")
        self.running = False

def main():
    parser = argparse.ArgumentParser(description='Timelapse with Raspberry Pi Camera')
    parser.add_argument('-i', '--interval', type=int, default=60,
                        help='Interval between photos in seconds (default: 60)')
    parser.add_argument('-o', '--output', type=str, default='timelapse',
                        help='Output folder for photos (default: timelapse)')
    
    args = parser.parse_args()
    
    camera = TimelapseCamera(interval=args.interval, output_dir=args.output)
    camera.start()

if __name__ == '__main__':
    main() 