#!/bin/bash
# Installation script for Face Recognition Attendance System
# Compatible with Raspberry Pi OS Debian 12 (bookworm) 64-bit

echo "🍓 Face Recognition Attendance System - Raspberry Pi Setup"
echo "=========================================================="

# Check if running on Raspberry Pi
if grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "✅ Detected Raspberry Pi system"
else
    echo "⚠️  Warning: This script is optimized for Raspberry Pi"
fi

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies for OpenCV and camera
echo "🔧 Installing system dependencies..."
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
    libcanberra-gtk3-module \
    libcanberra-gtk-module \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    ffmpeg

# Enable camera interface
echo "📹 Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python packages
echo "📚 Installing Python packages..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data
mkdir -p Attendance
mkdir -p static
mkdir -p templates

# Set proper permissions
echo "🔐 Setting permissions..."
chmod +x *.py
chmod 755 data
chmod 755 Attendance

# Create systemd service (optional)
echo "🔧 Would you like to create a systemd service for auto-start? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    SERVICE_FILE="/etc/systemd/system/face-attendance.service"
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Face Recognition Attendance System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable face-attendance.service
    echo "✅ Systemd service created and enabled"
fi

echo ""
echo "🎉 Installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Register faces: python add_faces_rpi.py"
echo "3. Start attendance system: python take_attendance_rpi.py"
echo "4. Start web interface: python app.py"
echo ""
echo "🌐 Web interface will be available at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "💡 Tips for Raspberry Pi:"
echo "   - Ensure good lighting for face recognition"
echo "   - Use a quality USB camera or Pi Camera"
echo "   - Consider using a heatsink for better performance"
echo "   - Check camera connection: vcgencmd get_camera"
