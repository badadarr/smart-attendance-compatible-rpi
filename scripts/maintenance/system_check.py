#!/usr/bin/env python3
"""
System Check and Diagnostic Tool for Face Recognition Attendance System
Compatible with Raspberry Pi OS Debian 12 (bookworm) 64-bit
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class SystemChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def log_error(self, message):
        self.errors.append(message)
        print(f"❌ {message}")

    def log_warning(self, message):
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def log_info(self, message):
        self.info.append(message)
        print(f"ℹ️  {message}")

    def log_success(self, message):
        print(f"✅ {message}")

    def check_system_info(self):
        """Check basic system information"""
        print("🔍 System Information Check")
        print("=" * 40)

        # OS Information
        self.log_info(f"Platform: {platform.platform()}")
        self.log_info(f"Python version: {sys.version}")
        self.log_info(f"Architecture: {platform.machine()}")

        # Check if Raspberry Pi
        try:
            with open("/proc/cpuinfo", "r") as f:
                content = f.read()
                if "Raspberry Pi" in content:
                    self.log_success("Running on Raspberry Pi")
                    # Extract Pi model
                    for line in content.split("\n"):
                        if "Model" in line:
                            self.log_info(line.strip())
                            break
                else:
                    self.log_warning("Not running on Raspberry Pi")
        except FileNotFoundError:
            self.log_warning("Cannot detect Raspberry Pi (proc/cpuinfo not found)")

        print()

    def check_camera(self):
        """Check camera availability"""
        print("📹 Camera Check")
        print("=" * 40)

        # Check camera detection command
        try:
            result = subprocess.run(
                ["vcgencmd", "get_camera"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                self.log_info(f"Camera status: {result.stdout.strip()}")
                if "detected=1" in result.stdout:
                    self.log_success("Camera detected by system")
                else:
                    self.log_error("No camera detected by system")
            else:
                self.log_warning("Cannot check camera status (vcgencmd not available)")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_warning("vcgencmd not available - cannot check Pi camera")

        # Check for USB cameras
        try:
            result = subprocess.run(
                ["lsusb"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                usb_devices = result.stdout
                camera_keywords = ["camera", "webcam", "usb", "video"]
                cameras_found = []
                for line in usb_devices.split("\n"):
                    for keyword in camera_keywords:
                        if keyword.lower() in line.lower() and "camera" in line.lower():
                            cameras_found.append(line.strip())
                            break

                if cameras_found:
                    self.log_success(
                        f"Found {len(cameras_found)} potential USB camera(s)"
                    )
                    for cam in cameras_found:
                        self.log_info(f"  - {cam}")
                else:
                    self.log_info("No obvious USB cameras detected")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.log_warning("Cannot check USB devices")

        # Check video devices
        video_devices = []
        for i in range(5):  # Check /dev/video0 to /dev/video4
            if os.path.exists(f"/dev/video{i}"):
                video_devices.append(f"/dev/video{i}")

        if video_devices:
            self.log_success(f"Video devices found: {', '.join(video_devices)}")
        else:
            self.log_error("No video devices found in /dev/")

        print()

    def check_python_dependencies(self):
        """Check Python package dependencies"""
        print("🐍 Python Dependencies Check")
        print("=" * 40)

        required_packages = {
            "cv2": "opencv-python",
            "sklearn": "scikit-learn",
            "numpy": "numpy",
            "pandas": "pandas",
            "flask": "Flask",
            "pickle": "built-in",
            "pathlib": "built-in",
        }

        optional_packages = {"pyttsx3": "pyttsx3 (for text-to-speech)"}

        for module, package in required_packages.items():
            try:
                __import__(module)
                if package == "built-in":
                    self.log_success(f"{module} (built-in)")
                else:
                    # Get version if possible
                    try:
                        mod = __import__(module)
                        version = getattr(mod, "__version__", "unknown")
                        self.log_success(f"{module} v{version}")
                    except:
                        self.log_success(f"{module} (installed)")
            except ImportError:
                self.log_error(f"Missing required package: {package}")

        for module, package in optional_packages.items():
            try:
                __import__(module)
                self.log_success(f"{module} (optional - installed)")
            except ImportError:
                self.log_warning(f"Optional package not installed: {package}")

        print()

    def check_file_structure(self):
        """Check required files and directories"""
        print("📁 File Structure Check")
        print("=" * 40)

        required_files = [
            "app.py",
            "add_faces_rpi.py",
            "take_attendance_rpi.py",
            "requirements.txt",
        ]

        required_dirs = ["templates", "data", "Attendance"]

        template_files = [
            "templates/base.html",
            "templates/index.html",
            "templates/daily_attendance.html",
            "templates/statistics.html",
        ]

        # Check required files
        for file in required_files:
            if os.path.exists(file):
                self.log_success(f"Found: {file}")
            else:
                self.log_error(f"Missing required file: {file}")

        # Check required directories
        for dir_name in required_dirs:
            if os.path.exists(dir_name) and os.path.isdir(dir_name):
                self.log_success(f"Found directory: {dir_name}")
            else:
                self.log_error(f"Missing required directory: {dir_name}")

        # Check template files
        for template in template_files:
            if os.path.exists(template):
                self.log_success(f"Found: {template}")
            else:
                self.log_warning(f"Missing template: {template}")

        # Check data files (optional at this stage)
        data_files = ["data/faces_data.pkl", "data/names.pkl"]
        for data_file in data_files:
            if os.path.exists(data_file):
                self.log_success(f"Found training data: {data_file}")
            else:
                self.log_info(
                    f"Training data not found: {data_file} (run add_faces_rpi.py first)"
                )

        print()

    def check_permissions(self):
        """Check file permissions"""
        print("🔐 Permissions Check")
        print("=" * 40)

        executable_files = [
            "app.py",
            "add_faces_rpi.py",
            "take_attendance_rpi.py",
            "install_rpi.sh",
        ]

        for file in executable_files:
            if os.path.exists(file):
                if os.access(file, os.X_OK):
                    self.log_success(f"{file} is executable")
                else:
                    self.log_warning(f"{file} is not executable (run: chmod +x {file})")
            else:
                self.log_info(f"{file} not found")

        # Check directory permissions
        dirs_to_check = ["data", "Attendance", "templates"]
        for dir_name in dirs_to_check:
            if os.path.exists(dir_name):
                if os.access(dir_name, os.R_OK | os.W_OK):
                    self.log_success(f"{dir_name} has read/write permissions")
                else:
                    self.log_error(f"{dir_name} lacks proper permissions")

        print()

    def check_system_resources(self):
        """Check system resources"""
        print("💾 System Resources Check")
        print("=" * 40)

        # Check available memory
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if "MemTotal" in line:
                        mem_kb = int(line.split()[1])
                        mem_mb = mem_kb // 1024
                        self.log_info(f"Total memory: {mem_mb} MB")
                        if mem_mb >= 2048:
                            self.log_success("Sufficient memory for face recognition")
                        elif mem_mb >= 1024:
                            self.log_warning(
                                "Minimal memory - consider reducing resolution"
                            )
                        else:
                            self.log_error("Insufficient memory for reliable operation")
                        break
        except FileNotFoundError:
            self.log_warning("Cannot check memory information")

        # Check disk space
        try:
            statvfs = os.statvfs(".")
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            free_mb = free_bytes // (1024 * 1024)
            self.log_info(f"Free disk space: {free_mb} MB")
            if free_mb >= 1024:
                self.log_success("Sufficient disk space")
            elif free_mb >= 512:
                self.log_warning("Low disk space - monitor usage")
            else:
                self.log_error("Very low disk space")
        except:
            self.log_warning("Cannot check disk space")

        # Check CPU temperature (Raspberry Pi)
        try:
            result = subprocess.run(
                ["vcgencmd", "measure_temp"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                temp_str = result.stdout.strip()
                self.log_info(f"CPU temperature: {temp_str}")
                # Extract temperature value
                temp_val = float(temp_str.split("=")[1].split("'")[0])
                if temp_val < 70:
                    self.log_success("CPU temperature is normal")
                elif temp_val < 80:
                    self.log_warning("CPU temperature is high - consider cooling")
                else:
                    self.log_error("CPU temperature is too high - add cooling!")
        except:
            self.log_info("Cannot check CPU temperature")

        print()

    def generate_report(self):
        """Generate final report"""
        print("📋 System Check Report")
        print("=" * 40)

        total_issues = len(self.errors) + len(self.warnings)

        if len(self.errors) == 0:
            self.log_success("No critical errors found!")
        else:
            print(f"❌ Critical errors found: {len(self.errors)}")
            for error in self.errors:
                print(f"   - {error}")

        if len(self.warnings) == 0:
            self.log_success("No warnings!")
        else:
            print(f"⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   - {warning}")

        print()
        if total_issues == 0:
            print("🎉 System is ready for face recognition attendance!")
            print("Next steps:")
            print("1. Run: python add_faces_rpi.py (to register faces)")
            print("2. Run: python take_attendance_rpi.py (for attendance)")
            print("3. Run: python app.py (for web interface)")
        else:
            print(f"🔧 Please resolve {total_issues} issue(s) before proceeding")

    def run_all_checks(self):
        """Run all system checks"""
        print("🍓 Face Recognition Attendance System - System Check")
        print("=" * 60)
        print()

        self.check_system_info()
        self.check_camera()
        self.check_python_dependencies()
        self.check_file_structure()
        self.check_permissions()
        self.check_system_resources()
        self.generate_report()


def main():
    """Main function"""
    checker = SystemChecker()
    checker.run_all_checks()


if __name__ == "__main__":
    main()
