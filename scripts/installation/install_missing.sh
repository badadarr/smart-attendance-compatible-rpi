#!/bin/bash
# Install missing system packages

echo "📦 Installing missing system packages..."

# Install libopencv-dev
sudo apt update
sudo apt install -y libopencv-dev

# Install psutil for performance monitoring
source venv/bin/activate
pip install psutil

echo "✅ Missing packages installed!"
echo ""
echo "📋 Installed:"
echo "   ✓ libopencv-dev (system package)"
echo "   ✓ psutil (Python package for performance monitoring)"
