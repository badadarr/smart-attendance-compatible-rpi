#!/bin/bash
# Quick fix script for common Raspberry Pi installation issues

echo "🚨 Emergency Fix for Raspberry Pi Installation"
echo "============================================="

# Check if we're on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  This script is designed for Raspberry Pi. Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        exit 1
    fi
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Install essential system packages
echo "📦 Installing essential system packages..."
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev build-essential

# Step 2: Create/activate virtual environment
if [ -d "venv" ]; then
    echo "🐍 Using existing virtual environment..."
    source venv/bin/activate
else
    echo "🐍 Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Step 3: Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Step 4: Try system packages first (most reliable on Pi)
echo "🎯 Installing Python packages via system repository..."
sudo apt install -y \
    python3-opencv \
    python3-numpy \
    python3-flask \
    python3-pandas \
    python3-pil

# Step 5: Install additional packages via pip (minimal set)
echo "📚 Installing additional packages via pip..."
pip install pyttsx3 werkzeug

# Step 6: Test installation
echo "🧪 Testing installation..."
python3 -c "
try:
    import cv2
    print('✅ OpenCV: OK')
except ImportError:
    print('❌ OpenCV: Failed')

try:
    import numpy
    print('✅ NumPy: OK')
except ImportError:
    print('❌ NumPy: Failed')

try:
    import flask
    print('✅ Flask: OK')
except ImportError:
    print('❌ Flask: Failed')

try:
    import pandas
    print('✅ Pandas: OK')
except ImportError:
    print('❌ Pandas: Failed')

try:
    import PIL
    print('✅ Pillow: OK')
except ImportError:
    print('❌ Pillow: Failed')
"

# Step 7: Test camera
echo "📹 Testing camera..."
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print('✅ Camera: Detected and working')
    cap.release()
else:
    print('❌ Camera: Not detected or not working')
    print('💡 Try: sudo raspi-config -> Interface Options -> Camera -> Enable')
"

# Step 8: Create minimal requirements file
echo "📝 Creating emergency requirements file..."
cat > requirements_emergency.txt << EOF
# Emergency minimal requirements - system packages preferred
# Only install via pip what's not available as system package

# Text-to-speech (not available as system package)
pyttsx3>=2.90

# Web framework (use system python3-flask when possible)
werkzeug>=2.0.0

# Note: Use these system packages instead of pip:
# sudo apt install python3-opencv python3-numpy python3-flask python3-pandas python3-pil
EOF

echo ""
echo "🎉 Emergency fix completed!"
echo ""
echo "📋 What was installed:"
echo "✓ System Python packages (more reliable on ARM)"
echo "✓ Minimal pip packages where needed"
echo "✓ Emergency requirements file created"
echo ""
echo "🔧 If you still have issues:"
echo "1. Reboot your Pi: sudo reboot"
echo "2. Check camera: vcgencmd get_camera"
echo "3. Run validation: python validate_setup.py"
echo ""
echo "💡 Pro tip: System packages (apt install python3-*) are usually"
echo "   more reliable on Raspberry Pi than pip packages"
