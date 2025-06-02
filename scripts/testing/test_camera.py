#!/usr/bin/env python3
"""
Camera Test Script for Face Recognition Attendance System
Tests camera functionality and face detection capabilities
"""

import cv2
import numpy as np
import sys
import time


def test_camera():
    """Test camera accessibility and basic functionality"""
    print("📹 Testing Camera Functionality")
    print("=" * 50)

    # Test multiple camera indices
    camera_indices = [0, 1, 2]
    working_cameras = []

    for idx in camera_indices:
        print(f"\n🔍 Testing camera index {idx}...")
        cap = cv2.VideoCapture(idx)

        if cap.isOpened():
            # Test frame capture
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"✅ Camera {idx}: Working - Resolution: {width}x{height}")
                working_cameras.append(idx)
            else:
                print(f"⚠️  Camera {idx}: Detected but cannot capture frames")
            cap.release()
        else:
            print(f"❌ Camera {idx}: Not accessible")

    return working_cameras


def test_face_detection(camera_idx=0):
    """Test face detection with live camera feed"""
    print(f"\n👤 Testing Face Detection with Camera {camera_idx}")
    print("=" * 50)

    # Load face cascade
    try:
        face_cascade = cv2.CascadeClassifier("data/haarcascade_frontalface_default.xml")
        if face_cascade.empty():
            print("❌ Could not load face cascade classifier")
            return False
        print("✅ Face cascade classifier loaded")
    except Exception as e:
        print(f"❌ Error loading face cascade: {e}")
        return False

    # Initialize camera
    cap = cv2.VideoCapture(camera_idx)
    if not cap.isOpened():
        print(f"❌ Cannot open camera {camera_idx}")
        return False

    print("\n📷 Starting face detection test...")
    print("Press 'q' to quit, 's' to save a test image")

    frame_count = 0
    faces_detected = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Cannot read frame from camera")
                break

            frame_count += 1

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.3, minNeighbors=5, minSize=(50, 50)
            )

            # Draw rectangles around faces
            for x, y, w, h in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                faces_detected += 1

            # Add info to frame
            cv2.putText(
                frame,
                f"Faces: {len(faces)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Frame: {frame_count}",
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "Press 'q' to quit",
                (10, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            # Display frame
            cv2.imshow("Face Detection Test", frame)

            # Check for key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("s"):
                # Save test image
                filename = f"test_capture_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Test image saved as {filename}")

            # Auto-quit after 100 frames for automated testing
            if frame_count >= 100:
                print("🔄 Auto-stopping after 100 frames")
                break

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Error during face detection test: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"\n📊 Test Results:")
    print(f"   Frames processed: {frame_count}")
    print(f"   Total faces detected: {faces_detected}")
    print(f"   Average faces per frame: {faces_detected/max(frame_count, 1):.2f}")

    return frame_count > 0


def main():
    print("🍓 Face Recognition Camera Test")
    print("Raspberry Pi Compatible Version")
    print("=" * 50)

    # Test camera accessibility
    working_cameras = test_camera()

    if not working_cameras:
        print("\n❌ No working cameras found!")
        print("\n💡 Troubleshooting tips:")
        print("   1. Check camera connection")
        print("   2. Enable camera: sudo raspi-config -> Interface Options -> Camera")
        print("   3. Reboot after enabling camera")
        print("   4. Check if camera is used by another process")
        sys.exit(1)

    print(f"\n✅ Found {len(working_cameras)} working camera(s): {working_cameras}")

    # Test face detection with first working camera
    primary_camera = working_cameras[0]
    print(f"\n🎯 Using camera {primary_camera} for face detection test")

    if test_face_detection(primary_camera):
        print("\n🎉 Camera test completed successfully!")
        print("\n📋 Next steps:")
        print("   1. Register faces: python add_faces_rpi.py")
        print("   2. Take attendance: python take_attendance_rpi.py")
        print("   3. Start web interface: python app.py")
    else:
        print("\n❌ Face detection test failed")
        print("Check camera and OpenCV installation")


if __name__ == "__main__":
    main()
