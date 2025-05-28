# Face Recognition Attendance System for Raspberry Pi 4

🍓 **Compatible with Raspberry Pi OS Debian 12 (bookworm) 64-bit**

A complete face recognition attendance system designed specifically for Raspberry Pi 4 Model B, featuring real-time face detection, attendance tracking, and a web-based dashboard.

## 🚀 Features

- **Real-time Face Recognition**: Uses OpenCV and scikit-learn for accurate face detection
- **Attendance Tracking**: Automatic clock-in/clock-out system
- **Web Dashboard**: Modern web interface for viewing attendance data
- **Voice Feedback**: Optional text-to-speech notifications
- **Data Export**: CSV export functionality for attendance records
- **Statistics**: Comprehensive attendance analytics
- **Raspberry Pi Optimized**: Performance tuned for RPi 4

## 📋 System Requirements

- **Hardware**: Raspberry Pi 4 Model B (2GB+ RAM recommended)
- **OS**: Raspberry Pi OS with desktop (Debian 12 bookworm, 64-bit)
- **Camera**: USB webcam or Raspberry Pi Camera Module
- **Storage**: 8GB+ microSD card (Class 10 recommended)

## 🔧 Quick Installation

### Method 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd smart-attendance-compatible-rpi

# Make installation script executable
chmod +x install_rpi.sh

# Run installation script
./install_rpi.sh
```

### Method 2: Manual Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv libopencv-dev python3-opencv \
    libatlas-base-dev libjasper-dev libqtgui4 libqt4-test \
    espeak espeak-data libespeak1 libespeak-dev

# Enable camera
sudo raspi-config nonint do_camera 0

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

## 🎯 Usage

### 1. Register Faces

```bash
# Activate virtual environment
source venv/bin/activate

# Register new users
python add_faces_rpi.py
```

- Look directly at the camera
- Move your head slightly (left, right, up, down)
- Ensure good lighting
- The system will capture 20 samples automatically

### 2. Start Attendance System

```bash
# Run face recognition attendance
python take_attendance_rpi.py
```

- Press **SPACE** to record attendance
- Press **'q'** to quit
- Face detection runs in real-time

### 3. Access Web Dashboard

```bash
# Start web server
python app.py
```

- Open browser: `http://[PI_IP_ADDRESS]:5000`
- View daily attendance, statistics, and export data

## 📁 Project Structure

```
smart-attendance-compatible-rpi/
├── app.py                      # Web dashboard application
├── add_faces_rpi.py           # Face registration system
├── take_attendance_rpi.py     # Main attendance system
├── requirements.txt           # Python dependencies
├── install_rpi.sh            # Installation script
├── README.md                 # This file
├── data/                     # Face data storage
│   ├── faces_data.pkl       # Encoded face features
│   ├── names.pkl            # User names
│   └── haarcascade_frontalface_default.xml
├── Attendance/              # CSV attendance files
├── templates/               # Web interface templates
│   ├── base.html
│   ├── index.html
│   ├── daily_attendance.html
│   └── statistics.html
└── static/                  # Web assets (auto-created)
```

## 🔧 Configuration

### Camera Settings
The system automatically detects and configures camera settings for optimal performance on Raspberry Pi:

- **Resolution**: 640x480 (optimized for RPi)
- **FPS**: 15 (reduces CPU load)
- **Buffer**: 1 (minimal latency)

### Recognition Settings
- **Confidence Threshold**: 60% (adjustable in code)
- **Recognition Cooldown**: 3 seconds (prevents duplicate entries)
- **Face Samples**: 20 per user (for accurate training)

## 🌐 Web Dashboard Features

### Home Page
- Real-time system status
- Today's attendance summary
- Quick navigation

### Daily Attendance
- Date-specific attendance records
- Clock-in/clock-out tracking
- Export to CSV

### Statistics
- Attendance patterns analysis
- User attendance rates
- Most common clock-in/out times

## 🛠️ Troubleshooting

### Camera Issues
```bash
# Check camera detection
vcgencmd get_camera

# Test camera
raspistill -o test.jpg

# Check USB cameras
lsusb
```

### Performance Optimization
```bash
# Monitor system resources
htop

# Check temperature
vcgencmd measure_temp

# GPU memory split (if using Pi Camera)
sudo raspi-config # Advanced Options > Memory Split > 128
```

### Common Solutions

1. **No camera found**: Check connections and enable camera interface
2. **Low FPS**: Reduce resolution or close other applications
3. **Recognition errors**: Ensure good lighting and retrain faces
4. **Web interface slow**: Use lightweight browser or reduce resolution

## 📊 Performance Notes

### Raspberry Pi 4 Optimization
- Uses efficient face detection algorithms
- Reduced image processing resolution
- Optimized camera buffer settings
- Minimal background processes

### Expected Performance
- **Face Detection**: 10-15 FPS
- **Recognition Accuracy**: 85-95% (good lighting)
- **Memory Usage**: ~150-300MB
- **CPU Usage**: 30-50% (single core)

## 🔒 Security Considerations

- Face data stored locally (not cloud-based)
- Encrypted pickle files for face features
- Web interface runs on local network only
- No external data transmission

## 📱 Mobile Access

Access the web dashboard from mobile devices:
1. Connect mobile to same WiFi network
2. Open browser: `http://[PI_IP_ADDRESS]:5000`
3. Responsive design works on all screen sizes

## 🔄 Auto-Start Setup

The installation script can create a systemd service for automatic startup:

```bash
# Enable auto-start
sudo systemctl enable face-attendance.service

# Start service
sudo systemctl start face-attendance.service

# Check status
sudo systemctl status face-attendance.service
```

## 📈 Future Enhancements

- [ ] Multiple camera support
- [ ] RFID/Card integration
- [ ] Email notifications
- [ ] Mobile app
- [ ] Cloud backup
- [ ] Advanced analytics
- [ ] API endpoints

## 🛠️ Advanced Tools

The system includes several advanced tools for monitoring, maintenance, and troubleshooting:

### Performance Monitor
```bash
python performance_monitor.py
# Real-time system monitoring
# Performance analysis and recommendations
# Health checks and alerts
```

### System Validation
```bash
python validate_setup.py
# Comprehensive setup validation
# Dependency verification
# Configuration checks
# Performance assessment
```

### Backup & Restore
```bash
./backup_restore.sh
# Interactive backup and restore
# Automated data management
# Training data preservation
```

### Troubleshooting
```bash
./troubleshoot.sh
# Automated issue detection
# Common problem fixes
# System optimization
```

### Service Management
```bash
# Enable auto-start service
sudo systemctl enable attendance-system
sudo systemctl start attendance-system

# Check service status
sudo systemctl status attendance-system
```

## 📊 System Monitoring

Monitor your system's performance in real-time:

```bash
# Start performance monitoring
python performance_monitor.py monitor

# Analyze historical performance
python performance_monitor.py analyze

# Quick health check
python performance_monitor.py health
```

## 💾 Data Management

### Backup Your Data
```bash
# Create backup
./backup_restore.sh backup

# List available backups
./backup_restore.sh list

# Export to CSV
./backup_restore.sh export
```

### Restore Data
```bash
# Interactive restore
./backup_restore.sh restore

# Restore specific backup
./backup_restore.sh restore backup_file.tar.gz
```

## 🔍 System Validation

Ensure your system is properly configured:

```bash
# Full validation
python validate_setup.py

# Quick validation
python validate_setup.py --quick
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenCV community for computer vision libraries
- Flask team for the web framework
- Raspberry Pi Foundation for the amazing hardware
- scikit-learn contributors for machine learning tools

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing issues
3. Create new issue with detailed description

---

**Made with ❤️ for Raspberry Pi 4 Model B**
