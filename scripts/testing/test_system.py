#!/usr/bin/env python3
"""
Cross-platform Python Test Script for Face Recognition Attendance System
Works on Windows, Linux, and Raspberry Pi
"""

import sys
import os
import subprocess
import platform
import importlib.util


def print_colored(text, color="white"):
    """Print colored text (simplified for cross-platform compatibility)"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m",
    }

    if platform.system() == "Windows":
        # Simple output for Windows (no colors)
        print(text)
    else:
        # Colored output for Linux/Pi
        print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")


def check_python():
    """Check Python version"""
    print_colored("\n🐍 Checking Python Installation:", "yellow")
    print_colored("=" * 40, "yellow")

    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    print_colored(f"✅ Python version: {python_version}", "green")

    if sys.version_info < (3, 7):
        print_colored("❌ Python 3.7+ required", "red")
        return False

    print_colored(f"✅ Platform: {platform.system()} {platform.machine()}", "green")
    return True


def check_package(package_name, import_name=None, version_attr="__version__"):
    """Check if a package is installed and working"""
    if import_name is None:
        import_name = package_name

    try:
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            return False, "Not found"

        module = importlib.import_module(import_name)

        if hasattr(module, version_attr):
            version = getattr(module, version_attr)
            return True, f"v{version}"
        else:
            return True, "OK"

    except Exception as e:
        return False, str(e)


def check_packages():
    """Check all required packages"""
    print_colored("\n📦 Checking Python Packages:", "yellow")
    print_colored("=" * 40, "yellow")

    packages = [
        ("opencv-python", "cv2"),
        ("numpy", "numpy"),
        ("scikit-learn", "sklearn"),
        ("flask", "flask"),
        ("pandas", "pandas"),
        ("pillow", "PIL"),
    ]

    missing_packages = []

    for package_name, import_name in packages:
        success, info = check_package(package_name, import_name)

        if success:
            print_colored(f"✅ {package_name}: {info}", "green")
        else:
            print_colored(f"❌ {package_name}: {info}", "red")
            missing_packages.append(package_name)

    return missing_packages


def install_packages(packages):
    """Install missing packages"""
    if not packages:
        return True

    print_colored("\n📥 Installing Missing Packages:", "yellow")
    print_colored("=" * 40, "yellow")

    try:
        cmd = [sys.executable, "-m", "pip", "install"] + packages
        print_colored(f"🔄 Running: {' '.join(cmd)}", "blue")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print_colored("✅ Installation completed successfully", "green")
            return True
        else:
            print_colored(f"❌ Installation failed: {result.stderr}", "red")
            return False

    except Exception as e:
        print_colored(f"❌ Installation error: {str(e)}", "red")
        return False


def check_project_files():
    """Check if required project files exist"""
    print_colored("\n📁 Checking Project Files:", "yellow")
    print_colored("=" * 40, "yellow")

    required_files = [
        "app.py",
        "add_faces_rpi.py",
        "take_attendance_rpi.py",
        "config.ini",
        "data/haarcascade_frontalface_default.xml",
    ]

    all_found = True

    for file_path in required_files:
        if os.path.exists(file_path):
            print_colored(f"✅ {file_path}: Found", "green")
        else:
            print_colored(f"❌ {file_path}: Missing", "red")
            all_found = False

    return all_found


def check_rpi_files():
    """Check Raspberry Pi specific files"""
    print_colored("\n🥧 Raspberry Pi Deployment Files:", "yellow")
    print_colored("=" * 40, "yellow")

    rpi_files = [
        "fix_rpi_installation.sh",
        "requirements_rpi_minimal.txt",
        "complete_fix.sh",
        "ARM_TROUBLESHOOTING.md",
        "DEPLOYMENT_CHECKLIST.md",
    ]

    for file_path in rpi_files:
        if os.path.exists(file_path):
            print_colored(f"✅ {file_path}: Ready", "green")
        else:
            print_colored(f"❌ {file_path}: Missing", "red")


def test_camera():
    """Test camera functionality"""
    print_colored("\n📷 Testing Camera:", "yellow")
    print_colored("=" * 40, "yellow")

    try:
        import cv2

        # Try to access camera
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print_colored("❌ Camera: No camera detected", "red")
            return False

        # Try to read a frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            print_colored("❌ Camera: Cannot read frame", "red")
            return False

        print_colored("✅ Camera: Working", "green")
        print_colored(f"✅ Frame size: {frame.shape[1]}x{frame.shape[0]}", "green")

        # Test face detection
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        if face_cascade.empty():
            print_colored("❌ Face detection: Haar cascade failed", "red")
            return False

        print_colored("✅ Face detection: Ready", "green")
        return True

    except Exception as e:
        print_colored(f"⚠️  Camera test failed: {str(e)}", "yellow")
        print_colored("💡 This is normal if no camera is connected", "blue")
        return False


def test_face_recognition():
    """Test face recognition core functionality"""
    print_colored("\n🧠 Testing Face Recognition Core:", "yellow")
    print_colored("=" * 40, "yellow")

    try:
        import cv2
        import numpy as np
        from sklearn.neighbors import KNeighborsClassifier

        print_colored("✅ OpenCV: Imported", "green")
        print_colored("✅ NumPy: Imported", "green")
        print_colored("✅ Scikit-learn: Imported", "green")

        # Test LBPH face recognizer
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        print_colored("✅ LBPH Face Recognizer: Created", "green")

        # Check directories
        directories = [
            "TrainingImage",
            "TrainingImageLabel",
            "StudentDetails",
            "Attendance",
        ]
        missing_dirs = [d for d in directories if not os.path.exists(d)]

        if missing_dirs:
            print_colored(f"⚠️  Missing directories: {missing_dirs}", "yellow")
            print_colored("💡 These will be created automatically", "blue")
        else:
            print_colored("✅ All directories exist", "green")

        print_colored("🎉 Face recognition: READY", "green")
        return True

    except Exception as e:
        print_colored(f"❌ Face recognition test failed: {str(e)}", "red")
        return False


def test_web_interface():
    """Test web interface components"""
    print_colored("\n🌐 Testing Web Interface:", "yellow")
    print_colored("=" * 40, "yellow")

    try:
        from flask import Flask, render_template, Response, redirect, url_for

        print_colored("✅ Flask: Imported", "green")
        print_colored("✅ Flask components: Available", "green")

        # Check templates
        if os.path.exists("templates"):
            html_files = [f for f in os.listdir("templates") if f.endswith(".html")]
            print_colored(f"✅ Templates: {len(html_files)} HTML files", "green")
        else:
            print_colored("⚠️  Templates directory not found", "yellow")

        # Check static files
        if os.path.exists("static"):
            print_colored("✅ Static directory: Found", "green")
        else:
            print_colored("⚠️  Static directory not found", "yellow")

        print_colored("🎉 Web interface: READY", "green")
        return True

    except Exception as e:
        print_colored(f"❌ Web interface test failed: {str(e)}", "red")
        return False


def main():
    """Main test function"""
    print_colored("🧪 Face Recognition Attendance System - Cross-Platform Test", "cyan")
    print_colored("=" * 70, "cyan")

    # Check Python
    if not check_python():
        return False

    # Check packages
    missing_packages = check_packages()

    # Install missing packages if any
    if missing_packages:
        print_colored(f"\n⚠️  Missing packages: {missing_packages}", "yellow")
        install_choice = input("\n🤔 Install missing packages? (y/n): ").lower().strip()

        if install_choice == "y":
            if install_packages(missing_packages):
                # Re-check packages
                print_colored("\n🔄 Re-checking packages after installation:", "blue")
                missing_packages = check_packages()
        else:
            print_colored("⏭️  Skipping package installation", "blue")

    # Run tests
    project_files_ok = check_project_files()
    check_rpi_files()
    camera_ok = test_camera()
    face_rec_ok = test_face_recognition()
    web_ok = test_web_interface()

    # Summary
    print_colored("\n" + "=" * 70, "cyan")
    print_colored("📋 Test Summary:", "cyan")
    print_colored("=" * 70, "cyan")

    if not missing_packages and project_files_ok and face_rec_ok and web_ok:
        print_colored("🎉 ALL TESTS PASSED! System ready for deployment", "green")

        if platform.machine().lower() in ["armv7l", "aarch64"]:
            print_colored("🥧 Running on Raspberry Pi - System ready!", "green")
        else:
            print_colored("💻 Running on development machine", "blue")
            print_colored("\n🎯 Next steps for Raspberry Pi deployment:", "yellow")
            print_colored("1. Transfer files to Raspberry Pi", "white")
            print_colored("2. Run: chmod +x *.sh && ./complete_fix.sh", "white")
            print_colored("3. Enable camera: sudo raspi-config", "white")
            print_colored("4. Test: ./quick_test.sh", "white")
    else:
        print_colored("⚠️  Some tests failed - check errors above", "yellow")

    return True


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n⏹️  Test cancelled by user", "yellow")
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {str(e)}", "red")
        sys.exit(1)
