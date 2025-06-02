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
- **🖥️ Touchscreen Support**: HDMI touchscreen compatible (no keyboard required)
- **🎯 Multiple Interfaces**: Desktop app, web interface, and auto-record modes

## 📁 Project Structure

```
smart-attendance-compatible-rpi/
├── 🎯 Core Applications
│   ├── app.py                    # Flask web dashboard
│   ├── add_faces_rpi.py         # Face registration system
│   ├── take_attendance_rpi.py   # Main attendance recognition
│   ├── config.ini               # System configuration
│   └── start.sh                 # Quick start menu
│
├── 📝 scripts/                  # All automation scripts
│   ├── installation/            # Setup and installation scripts
│   ├── troubleshooting/         # Problem fixing scripts
│   ├── maintenance/             # System maintenance tools
│   ├── testing/                 # Testing and diagnostic tools
│   └── README.md               # Scripts documentation
│
├── 📚 docs/                     # Documentation
│   ├── INSTALLATION_GUIDE.md    # Complete setup guide
│   ├── ARM_TROUBLESHOOTING.md   # Raspberry Pi specific help
│   ├── DEPLOYMENT_CHECKLIST.md  # Production checklist
│   └── README.md               # Documentation index
│
├── 🛠️ tools/                    # Utility tools
│   ├── pi_camera_wrapper.py     # Camera utilities
│   ├── fix_training_data.py     # Data repair tools
│   └── README.md               # Tools documentation
│
├── 📊 Data & Templates
│   ├── data/                    # Training data and models
│   ├── Attendance/              # CSV attendance files
│   ├── templates/               # HTML templates
│   └── static/                  # Web assets
│
└── ⚙️ Configuration
    ├── requirements.txt         # Python dependencies
    ├── attendance-system.service # Systemd service
    └── venv/                   # Virtual environment
```

## 🔧 Quick Installation

### Method 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd smart-attendance-compatible-rpi

# Make installation script executable
chmod +x scripts/installation/install_rpi.sh

# Run installation script
scripts/installation/install_rpi.sh
```

### Method 2: Using Quick Start Menu

```bash
# Make start script executable
chmod +x start.sh

# Run quick start menu
./start.sh
```

## 🎯 Quick Commands

| Task | Command |
|------|---------|
| **Start System** | `./start.sh` |
| **Install** | `scripts/installation/install_rpi.sh` |
| **Troubleshoot** | `scripts/troubleshooting/troubleshoot.sh` |
| **Validate Setup** | `python scripts/maintenance/validate_setup.py` |
| **Test Camera** | `python scripts/testing/test_camera.py` |
| **Backup Data** | `scripts/maintenance/backup_restore.sh` |
| **Register Faces** | `python add_faces_rpi.py` |
| **Take Attendance** | `python take_attendance_rpi.py` |
| **Web Dashboard** | `python app.py` |

## 📋 System Requirements

- **Hardware**: Raspberry Pi 4 Model B (2GB+ RAM recommended)
- **OS**: Raspberry Pi OS with desktop (Debian 12 bookworm, 64-bit)
- **Camera**: USB webcam or Raspberry Pi Camera Module
- **Storage**: 8GB+ microSD card (Class 10 recommended)

## 🚀 Quick Start Guide

### 1. Installation
```bash
scripts/installation/install_rpi.sh
```

### 2. Register Faces
```bash
python add_faces_rpi.py
```

### 3. Start Attendance System
```bash
./start.sh
# Choose option 1: Start Attendance Recognition
```

### 4. For Touchscreen Displays (No Keyboard)
```bash
./start.sh
# Choose option 2: Start Touchscreen Attendance (Touch Interface)
# OR choose option 4: Start Touchscreen Web Interface
```

### 5. Access Web Dashboard
```bash
./start.sh
# Choose option 3: Start Web Dashboard
# Open browser: http://your-pi-ip:5000
```

## 🖥️ Touchscreen Support

Perfect for HDMI display touchscreens - **no keyboard required!**

### Available Interfaces:

1. **Desktop Touchscreen App** (`take_attendance_touchscreen.py`)
   - ✅ Fullscreen touch interface
   - ✅ Large touch buttons (RECORD, AUTO MODE, EXIT)
   - ✅ Auto-record mode for hands-free operation
   - ✅ Visual feedback and status display

2. **Web Touchscreen Interface** (`app_touchscreen.py`)
   - ✅ Browser-based touch interface
   - ✅ Real-time video streaming
   - ✅ Multi-device access
   - ✅ Modern responsive UI

3. **Auto Record Mode**
   - ✅ Automatically saves attendance when face detected
   - ✅ Perfect for entrance/exit points
   - ✅ 5-second cooldown between recordings
   - ✅ No user interaction required

### Quick Start for Touchscreen:
```bash
# Desktop touch interface
./start.sh → Option 2

# Web touch interface  
./start.sh → Option 4 → Access via browser
```

**📖 Detailed Guide**: See [`TOUCHSCREEN_SOLUTIONS.md`](TOUCHSCREEN_SOLUTIONS.md)

## 🔧 Troubleshooting

### Quick Fixes
```bash
# General troubleshooting
scripts/troubleshooting/troubleshoot.sh

# Camera issues
scripts/troubleshooting/fix_camera_issues.sh

# Permission issues
scripts/troubleshooting/fix_permissions.sh

# Complete system repair
scripts/troubleshooting/complete_fix.sh
```

### Common Issues

| Problem | Solution |
|---------|----------|
| **Camera not detected** | `scripts/troubleshooting/fix_camera_issues.sh` |
| **NumPy errors** | `scripts/troubleshooting/fix_rpi_installation.sh` |
| **Permission denied** | `scripts/troubleshooting/fix_permissions.sh` |
| **Missing packages** | `scripts/installation/install_missing.sh` |

## 📚 Documentation

- **Complete Setup Guide**: [`docs/INSTALLATION_GUIDE.md`](docs/INSTALLATION_GUIDE.md)
- **Raspberry Pi Troubleshooting**: [`docs/ARM_TROUBLESHOOTING.md`](docs/ARM_TROUBLESHOOTING.md)
- **Production Deployment**: [`docs/DEPLOYMENT_CHECKLIST.md`](docs/DEPLOYMENT_CHECKLIST.md)
- **Scripts Documentation**: [`scripts/README.md`](scripts/README.md)

## 🛠️ Advanced Tools

### System Monitoring
```bash
python scripts/maintenance/performance_monitor.py
python scripts/maintenance/system_check.py
```

### Testing & Validation
```bash
python scripts/testing/test_system.py
python scripts/maintenance/validate_setup.py
```

### Data Management
```bash
scripts/maintenance/backup_restore.sh
python tools/fix_training_data.py
```

## 🌐 Web Interface

The system includes a modern web dashboard accessible at `http://your-pi-ip:5000`:

- **Dashboard**: Real-time attendance status
- **Daily Records**: View daily attendance
- **Statistics**: Attendance analytics and reports
- **Export**: Download attendance data as CSV

## 🔒 Service Mode

Install as a system service for auto-start on boot:

```bash
sudo cp attendance-system.service /etc/systemd/system/
sudo systemctl enable attendance-system
sudo systemctl start attendance-system
```

## 📞 Support

- **Project Issues**: Check [`docs/ARM_TROUBLESHOOTING.md`](docs/ARM_TROUBLESHOOTING.md)
- **Installation Problems**: Run `scripts/troubleshooting/troubleshoot.sh`
- **System Validation**: Run `python scripts/maintenance/validate_setup.py`

## 🎯 Development

### Project Structure
- **Core Apps**: Main application files in root directory
- **Scripts**: All automation in `scripts/` directory
- **Documentation**: All guides in `docs/` directory  
- **Tools**: Utilities in `tools/` directory

### Adding New Features
1. Add core functionality to main apps
2. Add installation steps to `scripts/installation/`
3. Add troubleshooting to `scripts/troubleshooting/`
4. Add tests to `scripts/testing/`
5. Update documentation in `docs/`

---

**🍓 Optimized for Raspberry Pi 4 with Raspberry Pi OS Debian 12 (bookworm) 64-bit**
