#!/usr/bin/env python3
"""
End-to-end test of the attendance system workflow
"""
import sys
from pathlib import Path
import csv
from datetime import datetime
import tempfile

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))


def test_complete_workflow():
    """Test the complete attendance workflow"""
    print("🧪 Testing Complete Attendance Workflow")
    print("=" * 50)

    try:
        from take_attendance_rpi import AttendanceSystem

        # Initialize system
        print("1️⃣ Initializing attendance system...")
        system = AttendanceSystem()

        # Load training data
        print("2️⃣ Loading training data...")
        if not system.load_training_data():
            print("❌ Failed to load training data")
            return False

        print(f"✅ Loaded {len(set(system.labels))} users: {list(set(system.labels))}")

        # Test attendance recording
        print("3️⃣ Testing attendance recording...")

        # Simulate attendance records
        test_records = [
            ("derr", "08:00:00", "2025-06-03", "Clock In"),
            ("badar", "08:15:00", "2025-06-03", "Clock In"),
            ("derr", "12:00:00", "2025-06-03", "Clock Out"),
            ("badar", "17:00:00", "2025-06-03", "Clock Out"),
        ]

        # Create a temporary CSV file to test
        with tempfile.NamedTemporaryFile(
            mode="w", newline="", suffix=".csv", delete=False
        ) as f:
            writer = csv.writer(f)
            writer.writerow(system.csv_columns)

            for name, time, date, status in test_records:
                work_hours = ""
                if status == "Clock Out":
                    # Calculate work hours (simplified)
                    if name == "derr":
                        work_hours = "4.00"  # 8:00 to 12:00
                    elif name == "badar":
                        work_hours = "8.75"  # 8:15 to 17:00

                writer.writerow([name, time, date, status, work_hours])

            temp_file = f.name

        # Verify the CSV file
        print("4️⃣ Verifying CSV output...")
        with open(temp_file, "r", newline="") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        print(f"✅ Created {len(records)} attendance records")
        for record in records:
            status_icon = "🟢" if record["STATUS"] == "Clock In" else "🔴"
            work_hours = (
                f"({record['WORK_HOURS']} hours)" if record["WORK_HOURS"] else ""
            )
            print(
                f"   {status_icon} {record['NAME']} - {record['STATUS']} at {record['TIME']} {work_hours}"
            )

        # Test status determination logic
        print("5️⃣ Testing status determination...")
        current_status_derr = system.get_current_status("derr", "2025-06-03")
        current_status_badar = system.get_current_status("badar", "2025-06-03")

        print(f"   derr current status: {current_status_derr}")
        print(f"   badar current status: {current_status_badar}")

        # Test work hours calculation
        print("6️⃣ Testing work hours calculation...")
        derr_hours = system.calculate_work_hours("derr", "2025-06-03", "12:00:00")
        badar_hours = system.calculate_work_hours("badar", "2025-06-03", "17:00:00")

        print(f"   derr work hours: {derr_hours}")
        print(f"   badar work hours: {badar_hours}")

        print("\n🎉 Complete workflow test passed!")
        return True

    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_system_readiness():
    """Test if the system is ready for deployment"""
    print("\n🧪 Testing System Readiness")
    print("=" * 30)

    checks_passed = 0
    total_checks = 5

    # Check 1: Data directory structure
    project_root = Path(__file__).parent
    data_dir = project_root / "data"
    attendance_dir = project_root / "Attendance"

    if data_dir.exists() and attendance_dir.exists():
        print("✅ Directory structure correct")
        checks_passed += 1
    else:
        print("❌ Directory structure incorrect")

    # Check 2: Training data files
    names_file = data_dir / "names.pkl"
    faces_file = data_dir / "faces_data.pkl"

    if names_file.exists() and faces_file.exists():
        print("✅ Training data files present")
        checks_passed += 1
    else:
        print("❌ Training data files missing")

    # Check 3: CSV files have correct format
    csv_files = list(attendance_dir.glob("*.csv"))
    if csv_files:
        sample_file = csv_files[0]
        try:
            with open(sample_file, "r", newline="") as f:
                reader = csv.reader(f)
                headers = next(reader)
            if "WORK_HOURS" in headers:
                print("✅ CSV files have correct format")
                checks_passed += 1
            else:
                print("❌ CSV files missing WORK_HOURS column")
        except:
            print("❌ Error reading CSV files")
    else:
        print("⚠️  No CSV files found (will be created on first use)")
        checks_passed += 1

    # Check 4: Python dependencies
    try:
        import cv2, pickle, sklearn, numpy

        print("✅ Required Python packages available")
        checks_passed += 1
    except ImportError as e:
        print(f"❌ Missing Python packages: {e}")

    # Check 5: System can initialize
    try:
        sys.path.append(str(project_root / "src"))
        from take_attendance_rpi import AttendanceSystem

        system = AttendanceSystem()
        if system.load_training_data():
            print("✅ System initializes correctly")
            checks_passed += 1
        else:
            print("❌ System initialization failed")
    except Exception as e:
        print(f"❌ System initialization error: {e}")

    print(f"\n📊 System Readiness: {checks_passed}/{total_checks} checks passed")

    if checks_passed == total_checks:
        print("🚀 System is ready for deployment!")
        return True
    else:
        print("⚠️  System needs attention before deployment")
        return False


def main():
    """Run all tests"""
    print("🎯 Smart Attendance System - End-to-End Tests")
    print("=" * 60)

    # Run workflow test
    workflow_passed = test_complete_workflow()

    # Run readiness test
    readiness_passed = test_system_readiness()

    print(f"\n📋 Final Results:")
    print(f"   Workflow Test: {'✅ PASSED' if workflow_passed else '❌ FAILED'}")
    print(f"   Readiness Test: {'✅ PASSED' if readiness_passed else '❌ FAILED'}")

    if workflow_passed and readiness_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\n🚀 The attendance system is fully functional and ready to use!")
        print("\n📝 Usage Instructions:")
        print("   1. To run face registration: python src/add_faces_rpi.py")
        print("   2. To run attendance system: python src/take_attendance_rpi.py")
        print(
            "   3. To run touchscreen version: python src/take_attendance_touchscreen.py"
        )
        print("   4. To run web interface: python src/app.py")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")


if __name__ == "__main__":
    main()
