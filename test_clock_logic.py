#!/usr/bin/env python3
"""
Test Clock In/Clock Out Logic Implementation
"""

import sys
import os

sys.path.append("src")

from app_touchscreen import WebAttendanceSystem
from datetime import datetime
import csv


def test_clock_logic():
    """Test the Clock In/Clock Out determination logic"""
    print("🧪 Testing Clock In/Clock Out Logic")
    print("=" * 50)

    # Initialize system
    system = WebAttendanceSystem()

    # Test data
    test_name = "Test User"
    test_date = datetime.now().strftime("%Y-%m-%d")
    test_time = datetime.now().strftime("%H:%M:%S")

    print(f"📅 Test Date: {test_date}")
    print(f"👤 Test User: {test_name}")
    print()

    # Test 1: No previous records (should be Clock In)
    print("🔍 Test 1: No previous records")
    status1 = system.determine_attendance_status(test_name, test_time, test_date)
    print(f"   Expected: Clock In")
    print(f"   Result: {status1}")
    print(f"   ✅ {'PASS' if status1 == 'Clock In' else 'FAIL'}")
    print()

    # Test 2: Create a test CSV with Clock In record
    print("🔍 Test 2: After Clock In record")
    test_file = system.attendance_dir / f"Attendance_{test_date}.csv"

    # Ensure directory exists
    system.attendance_dir.mkdir(exist_ok=True)

    # Create test record
    with open(test_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["NAME", "TIME", "DATE", "STATUS"])
        writer.writerow([test_name, "09:00:00", test_date, "Clock In"])

    status2 = system.determine_attendance_status(test_name, test_time, test_date)
    print(f"   Previous: Clock In")
    print(f"   Expected: Clock Out")
    print(f"   Result: {status2}")
    print(f"   ✅ {'PASS' if status2 == 'Clock Out' else 'FAIL'}")
    print()

    # Test 3: After Clock Out record
    print("🔍 Test 3: After Clock Out record")
    with open(test_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["NAME", "TIME", "DATE", "STATUS"])
        writer.writerow([test_name, "09:00:00", test_date, "Clock In"])
        writer.writerow([test_name, "17:00:00", test_date, "Clock Out"])

    status3 = system.determine_attendance_status(test_name, test_time, test_date)
    print(f"   Previous: Clock Out")
    print(f"   Expected: Clock In")
    print(f"   Result: {status3}")
    print(f"   ✅ {'PASS' if status3 == 'Clock In' else 'FAIL'}")
    print()

    # Test 4: Backward compatibility with Present status
    print("🔍 Test 4: Backward compatibility with 'Present' status")
    with open(test_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["NAME", "TIME", "DATE", "STATUS"])
        writer.writerow([test_name, "09:00:00", test_date, "Present"])

    status4 = system.determine_attendance_status(test_name, test_time, test_date)
    print(f"   Previous: Present")
    print(f"   Expected: Clock Out (backward compatibility)")
    print(f"   Result: {status4}")
    print(f"   ✅ {'PASS' if status4 == 'Clock Out' else 'FAIL'}")
    print()

    # Cleanup test file
    try:
        test_file.unlink()
        print("🧹 Test file cleaned up")
    except:
        pass

    print("=" * 50)
    print("🎯 Clock In/Clock Out Logic Test Complete!")

    # Summary
    all_tests = [
        status1 == "Clock In",
        status2 == "Clock Out",
        status3 == "Clock In",
        status4 == "Clock Out",
    ]

    passed = sum(all_tests)
    total = len(all_tests)

    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All tests PASSED! Clock In/Clock Out logic is working correctly.")
    else:
        print("❌ Some tests FAILED. Please check the implementation.")


if __name__ == "__main__":
    test_clock_logic()
