#!/bin/bash
# Quick test script untuk memastikan semua berfungsi setelah perbaikan

echo "🔧 Quick Test - Post Fix Validation"
echo "======================================"

# Test 1: Python imports
echo ""
echo "🐍 Testing Python Imports..."
python -c "
import cv2, numpy, sklearn, pandas, flask
print('✅ All critical packages imported successfully')
print(f'OpenCV: {cv2.__version__}')
print(f'NumPy: {numpy.__version__}')
print(f'scikit-learn: {sklearn.__version__}')
"

# Test 2: Camera
echo ""
echo "📹 Testing Camera..."
python -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f'✅ Camera working - Frame: {frame.shape}')
    else:
        print('❌ Cannot read frame')
    cap.release()
else:
    print('❌ Cannot open camera')
"

# Test 3: Face detection
echo ""
echo "👤 Testing Face Detection..."
python -c "
import cv2
from pathlib import Path

cascade_path = Path('data/haarcascade_frontalface_default.xml')
if cascade_path.exists():
    print('✅ Haar cascade file found')
    face_cascade = cv2.CascadeClassifier(str(cascade_path))
    print('✅ Face detection ready')
else:
    print('❌ Haar cascade file missing')
"

# Test 4: Fixed validation script
echo ""
echo "🔍 Testing Fixed Validation Script..."
python scripts/maintenance/validate_setup.py --quick

echo ""
echo "🎉 Quick test completed!"
echo ""
echo "📋 If all tests passed, proceed with:"
echo "   python add_faces_rpi.py      # Register first face"
echo "   python src/take_attendance_rpi.py # Test attendance"
echo "   ./start.sh                   # Start web interface"
