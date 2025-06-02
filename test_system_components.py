#!/usr/bin/env python3
"""
Simple test script to verify the attendance system components are working
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))


def test_training_data():
    """Test if training data loads correctly"""
    print("🧪 Testing training data loading...")

    try:
        from take_attendance_rpi import AttendanceSystem

        # Create system instance
        system = AttendanceSystem()

        # Test loading training data
        if system.load_training_data():
            print("✅ Training data loaded successfully")
            print(f"   - Total samples: {len(system.labels)}")
            print(f"   - Unique users: {len(set(system.labels))}")
            print(f"   - Users: {list(set(system.labels))}")
            return True
        else:
            print("❌ Failed to load training data")
            return False

    except Exception as e:
        print(f"❌ Error testing training data: {e}")
        return False


def test_csv_format():
    """Test CSV file creation and format"""
    print("\n🧪 Testing CSV format...")

    try:
        from take_attendance_rpi import AttendanceSystem
        import tempfile
        import csv
        from datetime import datetime

        # Create system instance
        system = AttendanceSystem()

        # Test CSV writing
        test_data = [
            ("John Doe", "08:00:00", "2025-06-03", "Clock In", ""),
            ("John Doe", "17:00:00", "2025-06-03", "Clock Out", "9.00"),
        ]

        # Create temporary file to test CSV format
        with tempfile.NamedTemporaryFile(
            mode="w", newline="", suffix=".csv", delete=False
        ) as f:
            writer = csv.writer(f)
            writer.writerow(system.csv_columns)
            writer.writerows(test_data)
            temp_file = f.name

        # Read back and verify
        with open(temp_file, "r", newline="") as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = list(reader)

        expected_headers = ["NAME", "TIME", "DATE", "STATUS", "WORK_HOURS"]
        if headers == expected_headers:
            print("✅ CSV format is correct")
            print(f"   - Headers: {headers}")
            print(f"   - Sample rows: {len(rows)}")
            return True
        else:
            print(f"❌ CSV format mismatch: {headers} vs {expected_headers}")
            return False

    except Exception as e:
        print(f"❌ Error testing CSV format: {e}")
        return False


def test_path_configuration():
    """Test if paths are correctly configured"""
    print("\n🧪 Testing path configuration...")

    try:
        from take_attendance_rpi import AttendanceSystem

        # Create system instance
        system = AttendanceSystem()

        print(f"📁 Data directory: {system.data_dir}")
        print(f"📁 Attendance directory: {system.attendance_dir}")
        print(f"📄 Names file: {system.names_file}")
        print(f"📄 Faces file: {system.faces_file}")

        # Check if files exist
        if system.names_file.exists() and system.faces_file.exists():
            print("✅ Training data files found")
            return True
        else:
            print("❌ Training data files not found")
            return False

    except Exception as e:
        print(f"❌ Error testing path configuration: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Smart Attendance System - Component Tests")
    print("=" * 50)

    tests_passed = 0
    total_tests = 3

    # Test 1: Training data
    if test_training_data():
        tests_passed += 1

    # Test 2: CSV format
    if test_csv_format():
        tests_passed += 1

    # Test 3: Path configuration
    if test_path_configuration():
        tests_passed += 1

    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! The system is ready to use.")
        print("\n🚀 To run the attendance system:")
        print("   python src/take_attendance_rpi.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
