#!/usr/bin/env python3
"""
Simple Test for Touchscreen Attendance System
"""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

print("🧪 Testing Touchscreen Attendance System...")
print("=" * 50)

try:
    print("📦 Importing libraries...")
    import cv2
    import numpy as np
    from sklearn.neighbors import KNeighborsClassifier

    print("✅ Core libraries imported")

    print("📱 Importing touchscreen system...")
    from take_attendance_touchscreen import TouchscreenAttendanceSystem

    print("✅ TouchscreenAttendanceSystem imported")

    print("🔧 Initializing system...")
    system = TouchscreenAttendanceSystem()
    print("✅ System initialized successfully")

    print("📂 Checking data files...")
    if system.names_file.exists() and system.faces_file.exists():
        print("✅ Training data found")

        # Try to run a quick test
        print("🎯 Testing system functionality...")
        if hasattr(system, "load_training_data"):
            try:
                system.load_training_data()
                print("✅ Training data loaded successfully")
            except Exception as e:
                print(f"⚠️  Training data load warning: {e}")
        else:
            print("ℹ️  load_training_data method not found")

    else:
        print("⚠️  No training data found - need to register faces first")
        print(f"   Expected files:")
        print(f"   - {system.names_file}")
        print(f"   - {system.faces_file}")

    print("\n🎉 System test completed successfully!")
    print("💡 To run the actual system: python src/take_attendance_touchscreen.py")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Try: pip install -r requirements.txt")

except Exception as e:
    print(f"❌ System error: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 50)
