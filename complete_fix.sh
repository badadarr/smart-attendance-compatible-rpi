#!/bin/bash
# Complete fix script for all validation issues

echo "🔧 Complete System Fix for Face Recognition Attendance"
echo "======================================================"

# Step 1: Fix permissions
echo "🔐 Step 1: Fixing file permissions..."
chmod +x *.sh
chmod +x *.py
echo "✅ Permissions fixed"

# Step 2: Install missing system packages  
echo "📦 Step 2: Installing missing system packages..."
sudo apt update
sudo apt install -y libopencv-dev
echo "✅ System packages installed"

# Step 3: Install missing Python packages
echo "🐍 Step 3: Installing missing Python packages..."
source venv/bin/activate
pip install psutil
echo "✅ Python packages installed"

# Step 4: Test camera access
echo "📹 Step 4: Testing camera access..."
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print('✅ Camera: Working properly')
    cap.release()
else:
    print('⚠️  Camera: Check connection or enable camera interface')
    print('   Run: sudo raspi-config -> Interface Options -> Camera -> Enable')
"

# Step 5: Validate setup again
echo "🧪 Step 5: Running validation..."
python validate_setup.py

echo ""
echo "🎉 All fixes applied!"
echo ""
echo "📋 Next steps:"
echo "1. If camera still not working: sudo raspi-config -> enable camera"
echo "2. Reboot Pi if camera was just enabled: sudo reboot"
echo "3. Test face registration: python add_faces_rpi.py"
echo "4. Start the system: python app.py"
echo ""
echo "🌐 Web interface will be at: http://$(hostname -I | awk '{print $1}'):5000"
