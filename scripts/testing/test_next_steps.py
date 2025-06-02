#!/usr/bin/env python3
"""
Next Steps Script - Automated testing and setup completion
For Face Recognition Attendance System on Raspberry Pi
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and report result"""
    print(f"\n🔧 {description}")
    print("=" * 50)

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print("❌ FAILED")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT - Command took too long")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_python_imports():
    """Test critical Python imports"""
    print("\n🐍 Testing Python Package Imports")
    print("=" * 50)

    imports = [
        ("import cv2; print('OpenCV version:', cv2.__version__)", "OpenCV"),
        ("import numpy as np; print('NumPy version:', np.__version__)", "NumPy"),
        (
            "import sklearn; print('scikit-learn version:', sklearn.__version__)",
            "scikit-learn",
        ),
        ("import pandas as pd; print('Pandas version:', pd.__version__)", "Pandas"),
        ("import flask; print('Flask version:', flask.__version__)", "Flask"),
    ]

    all_passed = True
    for import_cmd, package_name in imports:
        success = run_command(f'python -c "{import_cmd}"', f"Testing {package_name}")
        if not success:
            all_passed = False

    return all_passed


def test_camera():
    """Test camera functionality"""
    print("\n📹 Testing Camera Functionality")
    print("=" * 50)

    camera_test_cmd = '''python -c "
import cv2
import sys

print('Testing camera access...')
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print('❌ Cannot open camera')
    sys.exit(1)

# Test reading frames
ret, frame = cap.read()
if not ret:
    print('❌ Cannot read from camera')
    cap.release()
    sys.exit(1)

print('✅ Camera is working properly')
print(f'Frame size: {frame.shape[1]}x{frame.shape[0]}')

cap.release()
print('✅ Camera test completed successfully')
"'''

    return run_command(camera_test_cmd, "Camera Access Test")


def test_face_detection():
    """Test face detection functionality"""
    print("\n👤 Testing Face Detection")
    print("=" * 50)

    face_detection_cmd = '''python -c "
import cv2
import sys
from pathlib import Path

# Check for haar cascade file
cascade_path = Path('data/haarcascade_frontalface_default.xml')
if not cascade_path.exists():
    print('❌ Haar cascade file not found')
    sys.exit(1)

print('✅ Haar cascade file found')

# Test loading cascade
try:
    face_cascade = cv2.CascadeClassifier(str(cascade_path))
    print('✅ Face cascade loaded successfully')
except Exception as e:
    print(f'❌ Error loading cascade: {e}')
    sys.exit(1)

# Test camera and detection
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print('❌ Cannot open camera for face detection test')
    sys.exit(1)

ret, frame = cap.read()
if ret:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    print(f'✅ Face detection working - detected {len(faces)} face(s)')
else:
    print('❌ Cannot read frame for face detection')

cap.release()
print('✅ Face detection test completed')
"'''

    return run_command(face_detection_cmd, "Face Detection Test")


def run_validation_script():
    """Run the updated validation script"""
    print("\n🔍 Running System Validation")
    print("=" * 50)

    return run_command(
        "python scripts/maintenance/validate_setup.py", "System Validation"
    )


def main():
    """Main function to run all tests"""
    print("🚀 Face Recognition System - Next Steps Testing")
    print("=" * 60)

    # Change to project root directory
    script_dir = Path(__file__).parent.absolute()
    project_root = script_dir.parent.parent

    import os

    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")

    tests = [
        ("Python Imports", test_python_imports),
        ("Camera Test", test_camera),
        ("Face Detection", test_face_detection),
        ("System Validation", run_validation_script),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n" + "=" * 60)
        print(f"🧪 Running: {test_name}")
        print("=" * 60)

        success = test_func()
        results[test_name] = success

        if success:
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED")

    # Final report
    print(f"\n" + "=" * 60)
    print("📊 FINAL TEST REPORT")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} - {status}")

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 Next Steps:")
        print("1. Register first face: python add_faces_rpi.py")
        print("2. Start attendance system: ./start.sh")
        print("3. Access web interface: http://raspberry-pi-ip:5000")
    else:
        print(
            f"\n⚠️  {total - passed} test(s) failed. Please fix issues before proceeding."
        )
        print("\n🔧 Troubleshooting:")
        print("1. Check error messages above")
        print("2. Run: scripts/troubleshooting/troubleshoot.sh")
        print("3. Ensure camera is connected and enabled")


if __name__ == "__main__":
    main()
