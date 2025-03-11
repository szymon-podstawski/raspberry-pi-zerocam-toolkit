# Raspberry Pi Zero W - Camera Projects

This project contains two applications for camera handling on Raspberry Pi Zero W:
1. Live preview through web browser (app.py)
2. Timelapse with automatic video generation (app_2.py)
3. Timelapse with live preview (app_3.py)

## Quick Start Guide

### Live Preview (app.py)
```bash
# Run the live preview server
python3 app.py

# Access in your web browser
http://[raspberry_pi_ip]:5000
```

### Timelapse (app_2.py)
```bash
# Basic usage (photos every 60 seconds)
python3 app_2.py

# Custom interval (e.g., every 5 seconds)
python3 app_2.py -i 5

# Custom output folder
python3 app_2.py -o my_timelapse

# Custom interval and folder
python3 app_2.py -i 30 -o my_timelapse
```

The timelapse application will:
1. Take photos at specified intervals
2. Save them in the designated folder
3. Automatically generate a video when you stop the program (Ctrl+C)
4. The video will be saved as `timelapse_video_YYYYMMDD_HHMMSS.mp4`

## 3. Timelapse with Live Preview (app_3.py)

### Features
- Combines timelapse and live preview functionality in one application
- Takes high-resolution background photos (2304x1296)
- Simultaneously shows live preview in browser (800x600)
- Web interface with folder and interval information
- Runs in background using screen
- Automatic folder creation with timestamp

### Requirements
```bash
# Installing required system packages (recommended over pip)
sudo apt install -y python3-flask python3-opencv screen
```

### Running
```bash
# Basic usage (photos every 60 seconds)
screen -S timelapse_new python3 app_3.py

# Custom folder and interval (e.g., every 30 seconds)
screen -S timelapse_new python3 app_3.py -o timelapse_20240321 -i 30
```

### Managing Screen Session
```bash
# Detach from screen (program continues running)
Ctrl + A, then D

# Return to screen
screen -r timelapse_new

# List active screens
screen -ls

# End program
Ctrl + C
```

### Access
- Live preview: http://[raspberry_pi_ip]:5000
- Photos saved in folder: ~/kamera/[folder_name]
- Web interface shows:
  - Current save folder
  - Timelapse interval
  - Live camera preview

### Real-World Testing Results
- Successfully runs both timelapse and preview simultaneously
- Web preview remains smooth while taking high-res photos
- No interference between preview and photo capture
- Memory usage remains stable during long runs
- Can run for extended periods in background
- Easy to monitor through web interface

### Best Practices
1. Use screen for background operation
2. Create dated folders (e.g., timelapse_20240321)
3. Monitor through web interface
4. Check disk space regularly
5. Can safely close browser - program continues in background
6. Use system packages (apt) instead of pip for better stability

### Comparison with Previous Versions
This version (app_3.py) combines the best features of app.py and app_2.py:
- Live preview from app.py
- Timelapse capability from app_2.py
- Added features:
  - Background operation
  - Web status interface
  - Simultaneous preview and capture
  - Better error handling
  - Automatic folder creation

### Data Safety
- Photos are saved to SD card immediately after capture
- Sudden power loss won't damage saved photos
- Regular photo backup to computer recommended
- When using powerbank:
  - Use powerbank with battery level indicator
  - Consider using powerbank with pass-through charging
  - Monitor battery status

### Application Comparison
| Feature                 | app.py | app_2.py | app_3.py |
|------------------------|--------|----------|----------|
| Live preview           | ✓      | ✗        | ✓        |
| Timelapse              | ✗      | ✓        | ✓        |
| Background operation   | ✗      | ✗        | ✓        |
| Web interface          | ✓      | ✗        | ✓        |
| Custom interval        | ✗      | ✓        | ✓        |
| Custom save folder     | ✗      | ✓        | ✓        |

## Hardware Requirements
- Raspberry Pi Zero W
- Raspberry Pi compatible camera
- SSH connection to Raspberry Pi

### Camera Compatibility
This project uses the `picamera2` library, which supports the following cameras:
- Raspberry Pi Camera Module v2 (recommended)
- Raspberry Pi Camera Module v3
- Raspberry Pi HQ Camera
- Legacy Raspberry Pi Camera Module v1

⚠️ **Tested Hardware**:
This code has been successfully tested with:
- ZeroCam OV5647 5MPx Wide-angle 120° for Raspberry Pi Zero
  - Sensor: OV5647
  - Resolution: 5 megapixels
  - Field of view: 120 degrees
  - Compatible with both Raspberry Pi Zero and Zero W
  - Uses the same sensor as original Raspberry Pi Camera v1

Important notes:
- The camera must be connected via the CSI ribbon cable to the Raspberry Pi Zero W
- Make sure the ribbon cable is properly oriented (blue side facing the USB ports)
- The camera must be enabled in Raspberry Pi configuration
- This project does NOT support:
  - USB webcams
  - Third-party CSI cameras without proper Linux drivers
  - Cameras requiring custom interfaces

To verify your camera:
```bash
# Check if camera is detected
vcgencmd get_camera

# Should output something like:
# supported=1 detected=1
```

## Detailed Step-by-Step Installation

### 1. System Preparation
```bash
# System update
sudo apt update
sudo apt upgrade -y

# Installing basic tools
sudo apt install -y python3-full python3-pip git
```

### 2. Camera Library Installation
```bash
# Installing camera handling libraries
sudo apt install -y python3-picamera2
sudo apt install -y python3-opencv # optional, for additional features
```

### 3. Python Dependencies Installation
```bash
# Installing Python packages from requirements.txt
pip3 install -r requirements.txt
```

### 4. Additional System Tools Installation
```bash
# Installing ffmpeg for video generation
sudo apt install -y ffmpeg

# Installing screen for background running
sudo apt install -y screen
```

### 5. Camera Configuration
```bash
# Checking if camera is detected
v4l2-ctl --list-devices

# Adding user to video group (restart required)
sudo usermod -a -G video $USER

# Editing configuration
sudo nano /boot/config.txt
```
Add/uncomment the following lines in config.txt:
```
start_x=1
gpu_mem=128
camera_auto_detect=1
```

### 6. Project Download
```bash
# Creating project directory
mkdir ~/kamera
cd ~/kamera

# Copying project files
# Copy app.py and app_2.py to this directory
```

### 7. Creating Image Directories
```bash
# Creating directories for images
mkdir timelapse
mkdir moj_timelapse
```

### 8. Installation Verification
```bash
# Python test
python3 --version

# Flask test
python3 -c "import flask; print(flask.__version__)"

# picamera2 test
python3 -c "from picamera2 import Picamera2; print('Picamera2 OK')"

# ffmpeg test
ffmpeg -version
```

## Computer Installation (for video generation)

### Windows
1. Install FFmpeg:
```powershell
# Use winget (Windows 10/11)
winget install FFmpeg

# Or download from https://ffmpeg.org/download.html
```

2. Add FFmpeg to PATH variable:
- Open "System Settings" -> "Environment Variables"
- Add FFmpeg path to PATH variable

## 1. Live Preview (app.py)

### Features
- Real-time camera streaming
- Web browser access
- Resolution: 800x600 pixels
- 10 frames per second

### Running
```bash
# On Raspberry Pi:
python3 app.py

# Access through browser:
http://[raspberry_pi_ip]:5000
```

### Stopping
```bash
# In Raspberry Pi terminal:
Ctrl + C
```

## 2. Timelapse (app_2.py)

### Features
- Taking photos at specified intervals
- Automatic saving with timestamp
- Configurable interval
- High resolution photos (2304x1296)

### Running
```bash
# Basic usage (photos every 60 seconds):
python3 app_2.py

# Custom interval (e.g., every 5 seconds):
python3 app_2.py -i 5

# Custom folder:
python3 app_2.py -o my_timelapse

# Combining both options:
python3 app_2.py -i 30 -o my_timelapse
```

### Background Running (screen)
```bash
# Screen installation:
sudo apt install screen

# Creating new session:
screen -S timelapse

# Running application:
python3 app_2.py -i 60

# Detaching from session (program continues running):
Ctrl + A, then D

# Returning to session:
screen -r timelapse

# Ending session:
Ctrl + D
```

## Generating Video from Timelapse

⚠️ **Important Performance Note**:
Based on our real-world tests (599 frames to 25-second video):
- Processing on Raspberry Pi Zero W took 40 minutes
- Same process on PC takes just minutes
- File transfer time: ~1 minute for 110MB file
- Final video quality is identical regardless of generation method

### Method 1: Generating on Raspberry Pi (NOT RECOMMENDED)
```bash
# On Raspberry Pi:
ffmpeg -framerate 24 -pattern_type glob -i 'timelapse/*.jpg' -c:v libx264 -pix_fmt yuv420p timelapse_final.mp4

# WARNING: Very slow processing!
# Real test results:
# - 599 frames → 40 minutes processing
# - ~0.3 frames per second
# - High CPU usage
# - System becomes very unresponsive
```

### Method 2: Generating on Computer (RECOMMENDED)
```powershell
# In PowerShell on computer:
# 1. Create folder for photos
mkdir timelapse_photos

# 2. Copy photos from Raspberry Pi
scp admin@[raspberry_pi_ip]:~/kamera/timelapse/*.jpg timelapse_photos/

# 3. Generate video (much faster than on Raspberry Pi)
ffmpeg -framerate 24 -pattern_type glob -i "timelapse_photos/*.jpg" -c:v libx264 -preset ultrafast -pix_fmt yuv420p timelapse_final.mp4
```

### Method 3: Transferring Complete Video
If you already generated the video on Raspberry Pi:
```powershell
# In PowerShell on computer:
# Copy the generated video file (about 1 minute for 110MB file)
scp admin@[raspberry_pi_ip]:~/kamera/timelapse_final.mp4 C:\Users\[user]\Desktop
```

### Performance Tips
1. Always generate videos on a PC rather than Raspberry Pi Zero W
2. Use `-preset ultrafast` for faster processing
3. For better quality (but slower processing), remove the `-preset` parameter
4. If you have an NVIDIA GPU, you can use hardware acceleration:
   ```powershell
   ffmpeg -framerate 24 -pattern_type glob -i "timelapse_photos/*.jpg" -c:v h264_nvenc -preset p1 -pix_fmt yuv420p timelapse_final.mp4
   ```
5. For very large timelapses (thousands of photos), consider using Method 3 with tar
6. Network transfer speed is about 1.6MB/s on local network

## Configuration Parameters

### app.py
- Resolution: 800x600
- FPS: 10
- Port: 5000

### app_2.py
- Resolution: 2304x1296
- Default interval: 60 seconds
- File name format: timelapse_YYYYMMDD_HHMMSS.jpg

## Troubleshooting

1. If camera is not detected:
```bash
ls -l /dev/video*
v4l2-ctl --list-devices
```

2. Checking permissions:
```bash
sudo usermod -a -G video $USER
```

3. Checking camera configuration:
```bash
sudo nano /boot/config.txt
# Make sure you have:
start_x=1
gpu_mem=128
camera_auto_detect=1
```

## Real-World Performance Tests

Our practical tests with this setup showed:
1. **Photo Capture Performance**: Excellent
   - Reliable photo capture at specified intervals
   - High resolution (2304x1296) photos
   - Stable long-term operation

2. **Video Generation Performance**:
   - On Raspberry Pi Zero W (NOT RECOMMENDED):
     - 599 frames → 40 minutes processing time
     - ~0.3 frames per second processing speed
     - Final video: 25 seconds length, 111MB size
     - Very high CPU usage during processing
   - On PC (RECOMMENDED):
     - Same video generation takes minutes instead of hours
     - Much lower CPU usage
     - Better overall system responsiveness

3. **File Transfer Speed**:
   - ~1.6MB/s transfer speed over local network
   - 110MB video file transfer time: ~1 minute

Based on these results, we strongly recommend:
- Use Raspberry Pi Zero W for: photo capture, live streaming, camera control
- Use PC for: video generation, file processing, heavy computations 

## SD Card Management

### Monitoring Disk Space
```bash
# Check available space
df -h /

# Check size of photos folder
du -h ~/kamera/timelapse/
```

### Automatic Cleanup
To prevent SD card from filling up, you can:

1. Regularly copy and delete old photos:
```bash
# Copy photos to computer
scp admin@[raspberry_pi_ip]:~/kamera/timelapse/*.jpg backup_folder/

# Delete photos older than 7 days
find ~/kamera/timelapse/ -name "*.jpg" -mtime +7 -delete
```

2. Use automatic cleanup script:
```bash
# Delete photos when less than 1GB space remains
if [ $(df -P / | awk '/\// {print $4}') -lt 1000000 ]; then
    find ~/kamera/timelapse/ -name "*.jpg" -mtime +1 -delete
fi
```

### Recommendations
1. Use minimum 32GB SD card
2. Monitor space at least once daily
3. Space estimation:
   - Single photo ~2-3MB
   - 1000 photos = ~2-3GB
   - At 60s interval = ~50GB/day
4. Consider automatic copying to external drive or NAS 

## Basic File Operations

### Editing Files with Nano
```bash
# Open file in nano editor
nano app_3.py

# Nano keyboard shortcuts:
# Ctrl + O    - Save file
# Enter       - Confirm save
# Ctrl + X    - Exit nano
# Ctrl + K    - Cut line
# Ctrl + U    - Paste line
# Ctrl + W    - Search text
# Ctrl + G    - Show help
```

### Viewing Files
```bash
# View file content
cat app_3.py

# View last few lines
tail app_3.py

# View file with line numbers
nl app_3.py
```

### File Management
```bash
# List files
ls -l

# Check file size
du -h app_3.py

# Copy file
cp app_3.py app_3_backup.py

# Delete file
rm app_3_backup.py
```

These commands are essential for managing and editing your camera applications on Raspberry Pi. 