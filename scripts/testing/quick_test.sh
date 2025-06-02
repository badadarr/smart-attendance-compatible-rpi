#!/bin/bash
# Quick system test after installation fix

echo "🧪 Quick System Test - Face Recognition Attendance"
echo "================================================="

# Activate virtual environment
source venv/bin/activate

echo ""
echo "🔍 Testing Python Components:"
echo "-----------------------------"

# Test each component individually
echo -n "OpenCV: "
python3 -c "
import cv2
print(f'✅ OK (version {cv2.__version__})')
" 2>/dev/null || echo "❌ FAILED"

echo -n "NumPy: "
python3 -c "
import numpy as np
print(f'✅ OK (version {np.__version__})')
" 2>/dev/null || echo "❌ FAILED"

echo -n "Scikit-learn: "
python3 -c "
import sklearn
print(f'✅ OK (version {sklearn.__version__})')
" 2>/dev/null || echo "❌ FAILED"

echo -n "Flask: "
python3 -c "
import flask
print(f'✅ OK (version {flask.__version__})')
" 2>/dev/null || echo "❌ FAILED"

echo -n "Pandas: "
python3 -c "
import pandas as pd
print(f'✅ OK (version {pd.__version__})')
" 2>/dev/null || echo "❌ FAILED"

echo -n "Pillow: "
python3 -c "
import PIL
print(f'✅ OK (version {PIL.__version__})')
" 2>/dev/null || echo "❌ FAILED"

echo -n "psutil: "
python3 -c "
import psutil
print(f'✅ OK (version {psutil.__version__})')
" 2>/dev/null || echo "❌ FAILED"

echo ""
echo "📹 Testing Camera:"
echo "------------------"
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print('✅ Camera: Working perfectly (can capture frames)')
    else:
        print('⚠️  Camera: Detected but cannot capture frames')
    cap.release()
else:
    print('❌ Camera: Not detected or not accessible')
    print('💡 Try: sudo raspi-config -> Interface Options -> Camera -> Enable')
"

echo ""
echo "🔧 Testing System Files:"
echo "------------------------"
files_to_check=("data/haarcascade_frontalface_default.xml" "config/config.ini" "src/app.py" "src/add_faces_rpi.py" "src/take_attendance_rpi.py")

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file: Found"
    else
        echo "❌ $file: Missing"
    fi
done

echo ""
echo "🌐 Testing Network Ports:"
echo "-------------------------"
if ss -ln | grep -q ":5000 "; then
    echo "⚠️  Port 5000: Already in use"
else
    echo "✅ Port 5000: Available"
fi

echo ""
echo "📊 System Resources:"
echo "-------------------"
echo "💾 Memory: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2 " (" $5 " free)"}')"
echo "💿 Disk: $(df -h . | tail -1 | awk '{print $3 "/" $2 " (" $4 " free)"}')"
echo "🌡️  Temperature: $(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"

echo ""
echo "🎯 Ready to Test Face Recognition?"
echo "=================================="
echo "If all components show ✅, you can now:"
echo "1. Register faces: python add_faces_rpi.py"
echo "2. Take attendance: python src/take_attendance_rpi.py"
echo "3. Start web interface: python app.py"
echo ""
echo "🌐 Web interface will be at: http://$(hostname -I | awk '{print $1}'):5000"
