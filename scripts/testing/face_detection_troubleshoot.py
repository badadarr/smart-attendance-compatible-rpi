#!/usr/bin/env python3
"""
Face Detection Troubleshooter
Helps diagnose why face detection is showing 0 faces
"""

import cv2
import numpy as np
import os
import sys


def load_face_cascade():
    """Load and test face detection cascade"""
    print("🔍 Testing Face Detection Cascade:")
    print("-" * 40)

    # Try different cascade paths
    cascade_paths = [
        "data/haarcascade_frontalface_default.xml",
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml",
        "/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml",
        "/usr/local/share/opencv/haarcascades/haarcascade_frontalface_default.xml",
    ]

    for path in cascade_paths:
        if os.path.exists(path):
            print(f"✅ Found cascade: {path}")
            face_cascade = cv2.CascadeClassifier(path)

            if face_cascade.empty():
                print(f"❌ Cascade failed to load from: {path}")
            else:
                print(f"✅ Cascade loaded successfully from: {path}")
                return face_cascade, path
        else:
            print(f"❌ Not found: {path}")

    print("❌ No valid cascade found!")
    return None, None


def test_face_detection_on_image(image_path, face_cascade):
    """Test face detection on a specific image"""
    print(f"\n🖼️  Testing face detection on: {image_path}")
    print("-" * 50)

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return False

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Failed to load image: {image_path}")
        return False

    print(f"✅ Image loaded: {img.shape}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    print(f"✅ Converted to grayscale: {gray.shape}")

    # Test different detection parameters
    detection_configs = [
        {"scaleFactor": 1.1, "minNeighbors": 5, "minSize": (30, 30)},
        {"scaleFactor": 1.05, "minNeighbors": 3, "minSize": (20, 20)},
        {"scaleFactor": 1.3, "minNeighbors": 7, "minSize": (50, 50)},
        {"scaleFactor": 1.1, "minNeighbors": 3, "minSize": (15, 15)},
    ]

    best_result = 0
    best_config = None

    for i, config in enumerate(detection_configs):
        faces = face_cascade.detectMultiScale(gray, **config)
        print(
            f"  Config {i+1}: {len(faces)} faces (scale={config['scaleFactor']}, neighbors={config['minNeighbors']})"
        )

        if len(faces) > best_result:
            best_result = len(faces)
            best_config = config

    if best_result > 0:
        print(f"✅ Best result: {best_result} faces with config: {best_config}")

        # Draw faces on image and save
        faces = face_cascade.detectMultiScale(gray, **best_config)
        for x, y, w, h in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

        output_path = f"detected_faces_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, img)
        print(f"📸 Result saved: {output_path}")
        return True
    else:
        print("❌ No faces detected with any configuration")
        return False


def test_live_camera_detection():
    """Test face detection on live camera"""
    print("\n📹 Testing Live Camera Face Detection:")
    print("-" * 40)

    # Load cascade
    face_cascade, cascade_path = load_face_cascade()
    if face_cascade is None:
        print("❌ Cannot test without valid cascade")
        return False

    # Try Pi Camera wrapper first
    try:
        from pi_camera_wrapper import PiCameraWrapper

        camera = PiCameraWrapper()

        if camera.isOpened():
            print("✅ Using Pi Camera")
            ret, frame = camera.read()
            camera.release()

            if ret and frame is not None:
                return test_face_detection_on_frame(
                    frame, face_cascade, "pi_camera_frame.jpg"
                )

    except Exception as e:
        print(f"⚠️  Pi Camera failed: {str(e)}")

    # Fallback to USB camera
    for i in range(3):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()

                if ret:
                    print(f"✅ Using USB Camera {i}")
                    return test_face_detection_on_frame(
                        frame, face_cascade, f"usb_camera_{i}_frame.jpg"
                    )
        except:
            continue

    print("❌ No working camera found")
    return False


def test_face_detection_on_frame(frame, face_cascade, save_path):
    """Test face detection on a frame"""
    print(f"🎯 Testing face detection on live frame:")

    # Save original frame
    cv2.imwrite(save_path, frame)
    print(f"📸 Frame saved: {save_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Test detection
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
    )

    print(f"👤 Faces detected: {len(faces)}")

    if len(faces) > 0:
        # Draw rectangles around faces
        for x, y, w, h in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Save result
        result_path = f"detected_{save_path}"
        cv2.imwrite(result_path, frame)
        print(f"📸 Detection result saved: {result_path}")
        return True
    else:
        print("❌ No faces detected in live frame")

        # Save some debug info
        print("🔍 Debug information:")
        print(f"   Frame shape: {frame.shape}")
        print(f"   Frame dtype: {frame.dtype}")
        print(f"   Gray shape: {gray.shape}")
        print(f"   Gray min/max: {gray.min()}/{gray.max()}")

        return False


def check_lighting_conditions(image_path=None):
    """Check if lighting conditions are good for face detection"""
    print("\n💡 Checking Lighting Conditions:")
    print("-" * 40)

    if image_path and os.path.exists(image_path):
        img = cv2.imread(image_path)
        if img is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            print("❌ Cannot load test image")
            return
    else:
        # Use camera to get current lighting
        try:
            from pi_camera_wrapper import PiCameraWrapper

            camera = PiCameraWrapper()
            if camera.isOpened():
                ret, img = camera.read()
                camera.release()
                if ret:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    print("❌ Cannot capture frame for lighting check")
                    return
            else:
                print("❌ No camera available for lighting check")
                return
        except:
            print("❌ Cannot access camera for lighting check")
            return

    # Analyze lighting
    mean_brightness = np.mean(gray)
    std_brightness = np.std(gray)

    print(f"📊 Lighting Analysis:")
    print(f"   Mean brightness: {mean_brightness:.1f} (0-255)")
    print(f"   Brightness std: {std_brightness:.1f}")

    if mean_brightness < 50:
        print("⚠️  Too dark - increase lighting")
    elif mean_brightness > 200:
        print("⚠️  Too bright - reduce lighting")
    else:
        print("✅ Lighting looks good")

    if std_brightness < 20:
        print("⚠️  Low contrast - improve lighting variation")
    else:
        print("✅ Good contrast")


def main():
    print("🔍 Face Detection Troubleshooter")
    print("=" * 50)

    # Load and test cascade
    face_cascade, cascade_path = load_face_cascade()
    if face_cascade is None:
        print("\n❌ Cannot proceed without valid face cascade")
        return

    # Check for test images
    test_images = ["pi_camera_test.jpg", "wrapper_test.jpg"]
    found_images = [img for img in test_images if os.path.exists(img)]

    if found_images:
        print(f"\n🖼️  Found test images: {found_images}")
        for img in found_images:
            test_face_detection_on_image(img, face_cascade)
            check_lighting_conditions(img)

    # Test live camera
    test_live_camera_detection()

    # Recommendations
    print("\n💡 Troubleshooting Tips:")
    print("=" * 50)
    print("1. 💡 Ensure good lighting (not too dark/bright)")
    print("2. 👤 Position face directly toward camera")
    print("3. 📏 Keep face at reasonable distance (arm's length)")
    print("4. 🎯 Look directly at camera")
    print("5. 😐 Keep neutral expression (no extreme angles)")
    print("6. 🔄 Try different detection parameters")
    print("\n🔧 If still no detection:")
    print("   - Check camera focus")
    print("   - Test with different person")
    print("   - Verify cascade file integrity")


if __name__ == "__main__":
    main()
