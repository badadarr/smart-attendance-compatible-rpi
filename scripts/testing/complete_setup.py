#!/usr/bin/env python3
"""
Complete Setup Script for Face Recognition Attendance System
Handles the entire flow from validation to first face registration
"""

import subprocess
import sys
import os
from pathlib import Path
import time


class AttendanceSystemSetup:
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.project_root = self.script_dir.parent.parent

        # Change to project root
        os.chdir(self.project_root)

    def run_command(self, command, description, timeout=60):
        """Run a command with proper error handling"""
        print(f"\n🔧 {description}")
        print("-" * 50)

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                print("✅ SUCCESS")
                if result.stdout.strip():
                    print(result.stdout.strip())
                return True
            else:
                print("❌ FAILED")
                if result.stderr.strip():
                    print(f"Error: {result.stderr.strip()}")
                if result.stdout.strip():
                    print(f"Output: {result.stdout.strip()}")
                return False

        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT after {timeout} seconds")
            return False
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False

    def step1_validate_system(self):
        """Step 1: Run system validation"""
        print("\n" + "=" * 60)
        print("📋 STEP 1: System Validation")
        print("=" * 60)

        return self.run_command(
            "python scripts/maintenance/validate_setup.py --quick",
            "Running system validation",
        )

    def step2_test_camera(self):
        """Step 2: Test camera functionality"""
        print("\n" + "=" * 60)
        print("📹 STEP 2: Camera Testing")
        print("=" * 60)

        camera_cmd = '''python -c "
import cv2
print('Testing camera...')
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print('✅ Camera working - Frame size:', frame.shape)
    else:
        print('❌ Cannot read from camera')
    cap.release()
else:
    print('❌ Cannot open camera')
"'''
        return self.run_command(camera_cmd, "Testing camera access")

    def step3_test_face_detection(self):
        """Step 3: Test face detection"""
        print("\n" + "=" * 60)
        print("👤 STEP 3: Face Detection Testing")
        print("=" * 60)

        face_test_cmd = '''python -c "
import cv2
import numpy as np
from pathlib import Path

cascade_path = Path('data/haarcascade_frontalface_default.xml')
if not cascade_path.exists():
    print('❌ Haar cascade file missing')
    exit(1)

face_cascade = cv2.CascadeClassifier(str(cascade_path))
cap = cv2.VideoCapture(0)

if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        print(f'✅ Face detection ready - Found {len(faces)} face(s) in test frame')
    else:
        print('❌ Cannot capture test frame')
    cap.release()
else:
    print('❌ Cannot access camera for face detection test')
"'''
        return self.run_command(face_test_cmd, "Testing face detection")

    def step4_prepare_data_directory(self):
        """Step 4: Prepare data directory"""
        print("\n" + "=" * 60)
        print("📁 STEP 4: Data Directory Setup")
        print("=" * 60)

        # Create necessary directories
        dirs_to_create = [
            "data",
            "Attendance",
            "static/uploads",
            "static/css",
            "static/js",
        ]

        for directory in dirs_to_create:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {directory}")
            else:
                print(f"✅ Directory exists: {directory}")

        # Check for required files
        required_files = [
            "data/haarcascade_frontalface_default.xml",
            "config/config.ini",
        ]

        all_files_exist = True
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"✅ Required file exists: {file_path}")
            else:
                print(f"❌ Missing required file: {file_path}")
                all_files_exist = False

        return all_files_exist

    def step5_interactive_face_registration(self):
        """Step 5: Interactive face registration"""
        print("\n" + "=" * 60)
        print("👥 STEP 5: Face Registration")
        print("=" * 60)

        print(
            """
🎯 Ready to register your first face!

This process will:
1. Open your camera
2. Detect and capture your face
3. Save face data for recognition
4. Create initial attendance records

Make sure:
- Good lighting
- Face clearly visible 
- Look directly at camera
- Remove glasses if possible
        """
        )

        response = input("\n👤 Ready to register first face? (y/n): ").lower().strip()

        if response == "y":
            return self.run_command(
                "python add_faces_rpi.py", "Running face registration", timeout=120
            )
        else:
            print("⏭️  Skipping face registration for now")
            print("💡 You can register faces later with: python add_faces_rpi.py")
            return True

    def step6_start_system(self):
        """Step 6: Start the system"""
        print("\n" + "=" * 60)
        print("🚀 STEP 6: System Startup")
        print("=" * 60)

        print(
            """
🎉 Setup completed successfully!

You can now:
1. Start the attendance system: ./start.sh
2. Access web interface at: http://your-pi-ip:5000
3. Take attendance: python take_attendance_rpi.py
4. Add more faces: python add_faces_rpi.py
        """
        )

        response = input("\n🚀 Start the system now? (y/n): ").lower().strip()

        if response == "y":
            print("\n🌐 Starting web interface...")
            print("📍 Access at: http://localhost:5000")
            print("⏹️  Press Ctrl+C to stop")

            return self.run_command(
                "python app.py",
                "Starting web interface",
                timeout=5,  # Short timeout since this runs in background
            )
        else:
            print("✅ Setup completed! Start manually when ready.")
            return True

    def run_complete_setup(self):
        """Run the complete setup process"""
        print("🎯 Face Recognition Attendance System - Complete Setup")
        print("=" * 60)
        print(f"📁 Working in: {self.project_root}")

        steps = [
            ("System Validation", self.step1_validate_system),
            ("Camera Testing", self.step2_test_camera),
            ("Face Detection", self.step3_test_face_detection),
            ("Data Directory", self.step4_prepare_data_directory),
            ("Face Registration", self.step5_interactive_face_registration),
            ("System Startup", self.step6_start_system),
        ]

        completed_steps = 0

        for step_name, step_func in steps:
            print(f"\n" + "🔄 " + "=" * 58)
            print(f"📍 Current Step: {step_name}")
            print("=" * 60)

            try:
                success = step_func()

                if success:
                    print(f"✅ {step_name} - COMPLETED")
                    completed_steps += 1
                else:
                    print(f"❌ {step_name} - FAILED")

                    # Ask if user wants to continue
                    if step_name not in ["Face Registration", "System Startup"]:
                        response = (
                            input(f"\n⚠️  {step_name} failed. Continue anyway? (y/n): ")
                            .lower()
                            .strip()
                        )
                        if response != "y":
                            print("🛑 Setup aborted by user")
                            break
                        else:
                            completed_steps += 1
                    else:
                        # Optional steps can fail
                        completed_steps += 1

            except KeyboardInterrupt:
                print(f"\n🛑 Setup interrupted during {step_name}")
                break
            except Exception as e:
                print(f"❌ Unexpected error in {step_name}: {e}")
                break

        # Final report
        print(f"\n" + "=" * 60)
        print("📊 SETUP COMPLETION REPORT")
        print("=" * 60)
        print(f"Steps completed: {completed_steps}/{len(steps)}")

        if completed_steps == len(steps):
            print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("\n📋 Quick Reference:")
            print("• Start system: ./start.sh")
            print("• Add faces: python add_faces_rpi.py")
            print("• Take attendance: python take_attendance_rpi.py")
            print("• Web interface: http://your-pi-ip:5000")
            print("• Troubleshoot: scripts/troubleshooting/troubleshoot.sh")
        elif completed_steps >= 4:
            print("\n✅ Core setup completed with minor issues")
            print("📋 Manual steps needed:")
            print("• Register faces: python add_faces_rpi.py")
            print("• Start system: ./start.sh")
        else:
            print("\n⚠️  Setup incomplete - please resolve issues and retry")
            print("🔧 Troubleshooting: scripts/troubleshooting/troubleshoot.sh")


def main():
    """Main function"""
    setup = AttendanceSystemSetup()
    setup.run_complete_setup()


if __name__ == "__main__":
    main()
