#!/usr/bin/env python3
"""
Pi Camera Wrapper for Face Recognition System
Uses libcamera for Pi Camera Rev 1.3 compatibility
"""

import cv2
import subprocess
import os
import time
import tempfile


class PiCameraWrapper:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.is_pi_camera = self._detect_pi_camera()
        self.temp_dir = tempfile.mkdtemp()

    def _detect_pi_camera(self):
        """Detect if Pi Camera is available"""
        try:
            # Check if libcamera-still command exists
            result = subprocess.run(
                ["which", "libcamera-still"], capture_output=True, text=True
            )
            if result.returncode == 0:
                # Test if camera is actually working
                test_result = subprocess.run(
                    ["libcamera-still", "--list-cameras"],
                    capture_output=True,
                    text=True,
                )
                return "Available cameras" in test_result.stdout
        except:
            pass
        return False

    def isOpened(self):
        """Check if camera is available"""
        if self.is_pi_camera:
            return True
        else:
            # Fallback to USB camera
            cap = cv2.VideoCapture(self.camera_index)
            opened = cap.isOpened()
            cap.release()
            return opened

    def read(self):
        """Capture a frame"""
        if self.is_pi_camera:
            return self._capture_pi_camera()
        else:
            return self._capture_usb_camera()

    def _capture_pi_camera(self):
        """Capture from Pi Camera using libcamera-still"""
        try:
            # Create temporary file
            temp_file = os.path.join(self.temp_dir, f"capture_{int(time.time())}.jpg")

            # Capture with libcamera-still
            cmd = [
                "libcamera-still",
                "--output",
                temp_file,
                "--width",
                "640",
                "--height",
                "480",
                "--timeout",
                "1000",
                "--nopreview",
            ]

            result = subprocess.run(cmd, capture_output=True)

            if result.returncode == 0 and os.path.exists(temp_file):
                # Read the captured image
                frame = cv2.imread(temp_file)
                # Clean up
                os.remove(temp_file)
                return True, frame
            else:
                return False, None

        except Exception as e:
            print(f"Pi Camera capture error: {e}")
            return False, None

    def _capture_usb_camera(self):
        """Fallback to USB camera"""
        cap = cv2.VideoCapture(self.camera_index)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret, frame
        return False, None

    def release(self):
        """Release camera resources"""
        # Clean up temp directory
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


# Test function
def test_camera():
    print("🧪 Testing Pi Camera Wrapper")
    print("=" * 40)

    camera = PiCameraWrapper()

    if camera.isOpened():
        print(
            f"✅ Camera detected: {'Pi Camera' if camera.is_pi_camera else 'USB Camera'}"
        )

        # Test capture
        ret, frame = camera.read()
        if ret and frame is not None:
            print(f"✅ Frame captured: {frame.shape}")

            # Save test image
            test_file = "pi_camera_test.jpg"
            cv2.imwrite(test_file, frame)
            print(f"📸 Test image saved as: {test_file}")

            # Test face detection
            face_cascade = cv2.CascadeClassifier(
                "data/haarcascade_frontalface_default.xml"
            )
            if not face_cascade.empty():
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                print(f"👤 Faces detected: {len(faces)}")

        else:
            print("❌ Could not capture frame")
    else:
        print("❌ No camera detected")

    camera.release()


if __name__ == "__main__":
    test_camera()
