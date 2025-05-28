#!/bin/bash
# Fix script for Raspberry Pi installation issues
# Addresses ARM64 compatibility and package build problems

echo "🔧 Face Recognition Attendance System - Installation Fix"
echo "======================================================="

# Check if running on Raspberry Pi
if grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "✅ Detected Raspberry Pi system"
else
    echo "⚠️  Warning: This script is optimized for Raspberry Pi"
fi

# Get architecture info
ARCH=$(uname -m)
echo "📋 Architecture: $ARCH"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating existing virtual environment..."
    source venv/bin/activate
else
    echo "🐍 Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Upgrade pip and essential tools
echo "⬆️  Upgrading pip and build tools..."
pip install --upgrade pip setuptools wheel

# Install system packages for building (focusing on what's actually available)
echo "📦 Installing updated system dependencies..."
sudo apt update
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libtiff-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    libhdf5-dev \
    libhdf5-serial-dev \
    python3-h5py \
    espeak \
    espeak-data \
    libespeak1 \
    libespeak-dev \
    ffmpeg

# Try to install some packages that might be missing but have newer versions
echo "🔄 Installing updated package versions..."
sudo apt install -y \
    libilmbase25 \
    libopenexr25 \
    libwebp7 || echo "⚠️  Some packages might not be available, continuing..."

# Install pre-compiled wheels for ARM when possible
echo "🎯 Installing Python packages with ARM-optimized approach..."

# Install numpy first (using pre-compiled wheel if available)
echo "📊 Installing NumPy..."
pip install --only-binary=:all: "numpy>=1.21.0,<1.25.0" || pip install "numpy>=1.21.0,<1.25.0"

# Install scipy (try pre-compiled first)
echo "🧮 Installing SciPy..."
pip install --only-binary=:all: "scipy>=1.7.0,<1.12.0" || pip install "scipy>=1.7.0,<1.12.0"

# Install scikit-learn (try pre-compiled first)
echo "🤖 Installing scikit-learn..."
pip install --only-binary=:all: "scikit-learn>=1.0.0,<1.4.0" || pip install "scikit-learn>=1.0.0,<1.4.0"

# Install OpenCV (prefer pre-compiled)
echo "👁️  Installing OpenCV..."
pip install --only-binary=:all: "opencv-python>=4.5.0" || pip install "opencv-python-headless>=4.5.0"

# Install other required packages
echo "📚 Installing remaining packages..."
pip install \
    "Flask>=2.0.0" \
    "Werkzeug>=2.0.0" \
    "pandas>=1.3.0" \
    "Pillow>=8.0.0" \
    "pyttsx3>=2.90"

# Create alternative requirements file for future use
echo "📝 Creating alternative requirements file..."
cat > requirements_rpi_fixed.txt << EOF
# Fixed requirements for Raspberry Pi ARM64
# These versions are tested to work with ARM architecture

# Core packages with version ranges that work on ARM
numpy>=1.21.0,<1.25.0
scipy>=1.7.0,<1.12.0
scikit-learn>=1.0.0,<1.4.0

# OpenCV - prefer headless version for better compatibility
opencv-python-headless>=4.5.0

# Web framework
Flask>=2.0.0
Werkzeug>=2.0.0

# Data processing
pandas>=1.3.0

# Image processing
Pillow>=8.0.0

# Text-to-speech
pyttsx3>=2.90

# Build tools
setuptools>=60.0.0
wheel>=0.37.0
EOF

echo "✅ Alternative requirements file created: requirements_rpi_fixed.txt"

# Test the installation
echo "🧪 Testing installation..."
python -c "
try:
    import cv2
    print('✅ OpenCV imported successfully')
    import numpy as np
    print('✅ NumPy imported successfully')
    import sklearn
    print('✅ scikit-learn imported successfully')
    import pandas as pd
    print('✅ Pandas imported successfully')
    import flask
    print('✅ Flask imported successfully')
    print('🎉 All critical packages imported successfully!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('⚠️  Some packages may need manual installation')
"

echo ""
echo "🎉 Installation fix completed!"
echo ""
echo "📋 If you still have issues, try these alternative approaches:"
echo "1. Use the system's python3-opencv package:"
echo "   sudo apt install python3-opencv python3-numpy python3-scipy"
echo ""
echo "2. For minimal installation, create a simple requirements file:"
echo "   pip install opencv-python-headless flask pandas pillow"
echo ""
echo "3. Use piwheels (ARM-optimized packages):"
echo "   pip install --extra-index-url https://www.piwheels.org/simple/ -r requirements_rpi_fixed.txt"
echo ""
echo "💡 Next steps:"
echo "1. Test camera: python -c \"import cv2; cap=cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Error'); cap.release()\""
echo "2. Run validation: python validate_setup.py"
echo "3. If everything works, proceed with face registration"
