# INSTALLATION GUIDE
# Face Recognition Attendance System for Raspberry Pi 4
# Compatible with Raspberry Pi OS Debian 12 (bookworm) 64-bit

## 📋 COMPLETE FILE LIST

Your project should have these files:

### Core Application Files
- `app.py` - Web dashboard application
- `add_faces_rpi.py` - Face registration system  
- `take_attendance_rpi.py` - Main attendance recognition system

### Configuration and Setup
- `requirements.txt` - Python package dependencies
- `config.ini` - System configuration file
- `README.md` - Complete documentation

### Installation and Management Scripts
- `install_rpi.sh` - Automated installation script
- `start.sh` - Quick start menu system
- `troubleshoot.sh` - Troubleshooting and fixes
- `system_check.py` - System diagnostic tool

### Directories
- `data/` - Face recognition training data
- `Attendance/` - CSV attendance files
- `templates/` - Web interface HTML templates
- `static/` - Web assets (auto-created)

## 🚀 STEP-BY-STEP INSTALLATION

### Step 1: Initial Setup on Raspberry Pi

```bash
# Update your Raspberry Pi OS
sudo apt update && sudo apt upgrade -y

# Clone or copy your project files to Raspberry Pi
# If using git:
# git clone <your-repository-url>
# cd smart-attendance-compatible-rpi

# If copying files manually, ensure all files are in the project directory
```

### Step 2: Run Automated Installation

```bash
# Make installation script executable
chmod +x install_rpi.sh

# Run the installation script
./install_rpi.sh
```

The script will:
- Install system dependencies
- Enable camera interface
- Create Python virtual environment
- Install Python packages
- Set up directories and permissions
- Optionally create systemd service

### Step 3: Verify Installation

```bash
# Run system check
python system_check.py
```

This will verify:
- System compatibility
- Camera availability
- Python dependencies
- File structure
- Permissions
- System resources

### Step 4: Register Faces

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Register faces
python add_faces_rpi.py
```

Follow the on-screen instructions:
- Enter user name
- Look at camera for 60 seconds
- Move head slightly for variety
- System captures 20 samples automatically

### Step 5: Test the System

```bash
# Test attendance recognition
python take_attendance_rpi.py
```

Controls:
- Press **SPACE** to record attendance
- Press **'q'** to quit
- System shows live video with face detection

### Step 6: Start Web Interface

```bash
# Start web dashboard
python app.py
```

Access at: `http://[RASPBERRY_PI_IP]:5000`

## 🛠️ MANUAL INSTALLATION (If Automated Fails)

### Install System Dependencies

```bash
sudo apt install -y \
    python3-pip \
    python3-venv \
    libopencv-dev \
    python3-opencv \
    libatlas-base-dev \
    libjasper-dev \
    libqtgui4 \
    libqt4-test \
    libhdf5-dev \
    libhdf5-serial-dev \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libjasper1 \
    libilmbase23 \
    libopenexr23 \
    libgstreamer1.0-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgtk-3-dev \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    ffmpeg
```

### Enable Camera

```bash
# Enable camera interface
sudo raspi-config nonint do_camera 0

# Add camera configuration to boot config
echo "start_x=1" | sudo tee -a /boot/config.txt
echo "gpu_mem=128" | sudo tee -a /boot/config.txt

# Reboot to apply changes
sudo reboot
```

### Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python packages
pip install -r requirements.txt
```

### Create Directories

```bash
mkdir -p data Attendance templates static
chmod 755 data Attendance templates static
```

## ⚡ QUICK START (After Installation)

Use the quick start script for easy access:

```bash
# Make start script executable
chmod +x start.sh

# Run quick start menu
./start.sh
```

Options available:
1. Start Attendance Recognition
2. Start Web Dashboard Only  
3. Register New Faces
4. System Check
5. Exit

## 🔧 TROUBLESHOOTING

If you encounter issues, use the troubleshooting script:

```bash
# Make troubleshoot script executable
chmod +x troubleshoot.sh

# Run troubleshooting menu
./troubleshoot.sh
```

Available fixes:
- Camera permissions and setup
- Missing system packages
- Python virtual environment issues
- File permissions
- Memory issues
- System updates
- Temperature monitoring

## 📞 COMMON ISSUES AND SOLUTIONS

### Issue: "No camera detected"
**Solution:**
```bash
# Check camera hardware
vcgencmd get_camera

# Enable camera if needed
sudo raspi-config nonint do_camera 0

# Check video devices
ls /dev/video*

# Fix permissions
sudo usermod -a -G video $USER
```

### Issue: "ImportError: No module named 'cv2'"
**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall OpenCV
pip uninstall opencv-python
pip install opencv-python==4.8.1.78
```

### Issue: "Permission denied" errors
**Solution:**
```bash
# Fix file permissions
chmod +x *.py *.sh
chmod 755 data Attendance templates

# Fix camera permissions
sudo usermod -a -G video $USER
sudo chmod 666 /dev/video*
```

### Issue: "Low memory" or system slow
**Solution:**
```bash
# Clear system cache
sudo sync
sudo sysctl vm.drop_caches=3

# Enable swap if not active
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Close unnecessary applications
sudo pkill chromium firefox
```

### Issue: "High CPU temperature"
**Solution:**
- Add heatsink or fan to Raspberry Pi
- Reduce camera resolution in config.ini
- Close other running applications
- Check: `vcgencmd measure_temp`

## 🌐 NETWORK ACCESS

To access web dashboard from other devices:

1. Find Raspberry Pi IP address:
```bash
hostname -I
```

2. Open browser on any device connected to same network:
```
http://[RASPBERRY_PI_IP]:5000
```

3. For external access (advanced):
- Configure port forwarding on router
- Use dynamic DNS service
- Consider VPN for security

## 📊 PERFORMANCE OPTIMIZATION

For better performance on Raspberry Pi 4:

1. **Reduce camera resolution** (in config.ini):
```ini
FRAME_WIDTH = 320
FRAME_HEIGHT = 240
```

2. **Process fewer frames**:
```ini
PROCESS_EVERY_N_FRAMES = 10
```

3. **Enable GPU memory split**:
```bash
sudo raspi-config
# Advanced Options > Memory Split > 128
```

4. **Use faster SD card** (Class 10 or better)

5. **Ensure adequate power supply** (5V 3A recommended)

## 🔒 SECURITY CONSIDERATIONS

- Face data stored locally (not uploaded to cloud)
- Web interface accessible only on local network
- No external data transmission by default
- Consider firewall configuration for production use

## 📱 MOBILE COMPATIBILITY

The web interface is responsive and works on:
- Mobile phones (iOS/Android)
- Tablets
- Desktop computers
- All modern web browsers

## 🎯 NEXT STEPS

After successful installation:

1. **Register all users** with `add_faces_rpi.py`
2. **Train system** with good lighting conditions
3. **Test recognition** in actual usage environment
4. **Configure automatic startup** (systemd service)
5. **Set up data backup** procedures
6. **Monitor system performance** regularly

## 📈 SYSTEM MONITORING

Monitor your system regularly:

```bash
# Check system status
python system_check.py

# Monitor temperature
watch vcgencmd measure_temp

# Check memory usage
htop

# View system logs
journalctl -u face-attendance.service
```

## 🔄 UPDATES AND MAINTENANCE

Regular maintenance tasks:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip list --outdated
pip install --upgrade package_name

# Clean temporary files
./troubleshoot.sh
# Select option 5 (Clean up temporary files)

# Backup attendance data
cp -r Attendance/ /path/to/backup/
```

---

**🍓 Optimized for Raspberry Pi 4 Model B with Raspberry Pi OS Debian 12 (bookworm) 64-bit**
