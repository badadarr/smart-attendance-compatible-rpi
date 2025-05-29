#!/usr/bin/env python3
"""
Enhanced Camera Test for Raspberry Pi
Tests both Pi Camera and USB Camera with fallback
"""

import cv2
import subprocess
import os
import sys

def test_libcamera():
    """Test libcamera functionality"""
    print("🧪 Testing libcamera (Pi Camera):")
    print("-" * 40)
    
    try:
        # Test libcamera detection
        result = subprocess.run(
            ["libcamera-still", "--list-cameras"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ libcamera command available")
            print(f"📋 Output: {result.stdout.strip()}")
        else:
            print("❌ libcamera command failed")
            print(f"📋 Error: {result.stderr.strip()}")
            
    except subprocess.TimeoutExpired:
        print("⏰ libcamera test timeout")
    except Exception as e:
        print(f"❌ libcamera test error: {str(e)}")

def test_vcgencmd():
    """Test camera status via vcgencmd"""
    print("\n🔍 Testing vcgencmd (Camera Status):")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            ["vcgencmd", "get_camera"],
            capture_output=True,
            text=True
        )
        
        print(f"📋 Camera status: {result.stdout.strip()}")
        
        if "detected=1" in result.stdout:
            print("✅ Camera hardware detected")
        else:
            print("⚠️  Camera hardware not detected")
            
    except Exception as e:
        print(f"❌ vcgencmd error: {str(e)}")

def test_video_devices():
    """Test available video devices"""
    print("\n📹 Testing Video Devices:")
    print("-" * 40)
    
    video_devices = []
    for i in range(5):  # Check video0 to video4
        device = f"/dev/video{i}"
        if os.path.exists(device):
            video_devices.append(device)
            
    if video_devices:
        print(f"✅ Found video devices: {video_devices}")
        
        for device in video_devices:
            try:
                cap = cv2.VideoCapture(device)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        print(f"✅ {device}: Working ({frame.shape})")
                    else:
                        print(f"⚠️  {device}: Opened but can't read")
                    cap.release()
                else:
                    print(f"❌ {device}: Cannot open")
            except Exception as e:
                print(f"❌ {device}: Error - {str(e)}")
    else:
        print("❌ No video devices found")

def test_pi_camera_wrapper():
    """Test our Pi Camera wrapper"""
    print("\n🎯 Testing Pi Camera Wrapper:")
    print("-" * 40)
    
    try:
        from pi_camera_wrapper import PiCameraWrapper
        
        camera = PiCameraWrapper()
        
        if camera.isOpened():
            print("✅ Pi Camera Wrapper: Camera detected")
            
            ret, frame = camera.read()
            if ret and frame is not None:
                print(f"✅ Frame captured: {frame.shape}")
                
                # Save test image
                cv2.imwrite("wrapper_test.jpg", frame)
                print("📸 Test image saved: wrapper_test.jpg")
            else:
                print("❌ Failed to capture frame")
                
            camera.release()
        else:
            print("❌ Pi Camera Wrapper: No camera detected")
            
    except ImportError:
        print("❌ Pi Camera Wrapper: Import error")
    except Exception as e:
        print(f"❌ Pi Camera Wrapper: Error - {str(e)}")

def test_usb_camera_fallback():
    """Test USB camera as fallback"""
    print("\n🔌 Testing USB Camera Fallback:")
    print("-" * 40)
    
    for i in range(3):  # Test first 3 camera indices
        try:
            cap = cv2.VideoCapture(i)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"✅ USB Camera {i}: Working ({frame.shape})")
                    cv2.imwrite(f"usb_camera_{i}_test.jpg", frame)
                    print(f"📸 Test image saved: usb_camera_{i}_test.jpg")
                    cap.release()
                    return i  # Return working camera index
                else:
                    print(f"⚠️  USB Camera {i}: Opened but can't read")
                cap.release()
            else:
                print(f"❌ USB Camera {i}: Cannot open")
                
        except Exception as e:
            print(f"❌ USB Camera {i}: Error - {str(e)}")
    
    return None

def recommend_solution():
    """Recommend best camera solution"""
    print("\n💡 Recommendations:")
    print("=" * 50)
    
    # Test which cameras work
    pi_camera_works = False
    usb_camera_works = False
    
    try:
        from pi_camera_wrapper import PiCameraWrapper
        camera = PiCameraWrapper()
        if camera.isOpened():
            ret, frame = camera.read()
            pi_camera_works = ret and frame is not None
        camera.release()
    except:
        pass
    
    # Test USB camera
    working_usb = test_usb_camera_fallback()
    usb_camera_works = working_usb is not None
    
    print(f"\n📊 Summary:")
    print(f"   Pi Camera: {'✅ Working' if pi_camera_works else '❌ Not working'}")
    print(f"   USB Camera: {'✅ Working' if usb_camera_works else '❌ Not working'}")
    
    if pi_camera_works:
        print("\n🎯 RECOMMENDATION: Use Pi Camera")
        print("   - Pi Camera is working correctly")
        print("   - Continue with current setup")
        print("   - Run: python app.py")
        
    elif usb_camera_works:
        print("\n🎯 RECOMMENDATION: Switch to USB Camera")
        print("   - Pi Camera has issues, USB camera works")
        print("   - More reliable for face recognition")
        print("   - Update config.ini to use USB camera")
        
    else:
        print("\n🎯 RECOMMENDATION: Fix Hardware Issues")
        print("   - Check Pi Camera ribbon cable connection")
        print("   - Try different USB camera")
        print("   - Run camera fix script: ./fix_camera_issues.sh")

def main():
    print("🧪 Comprehensive Camera Test - Raspberry Pi")
    print("=" * 50)
    
    # Run all tests
    test_libcamera()
    test_vcgencmd()
    test_video_devices()
    test_pi_camera_wrapper()
    
    # Give recommendations
    recommend_solution()
    
    print("\n✅ Camera audit completed!")

if __name__ == "__main__":
    main()
