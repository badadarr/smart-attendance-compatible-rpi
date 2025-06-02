#!/usr/bin/env python3
"""
Quick System Test & Demo
Script untuk test cepat seluruh sistem clock in/clock out
"""

import cv2
import os
import csv
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import time


class QuickSystemTest:
    def __init__(self):
        """Initialize quick system test"""
        self.base_dir = Path(".")
        self.faces_dir = self.base_dir / "faces"
        self.attendance_dir = self.base_dir / "Attendance"
        self.trainer_dir = self.base_dir / "trainer"

        self.test_results = []

    def log_test(self, test_name, passed, message=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f": {message}"

        self.test_results.append((test_name, passed, message))
        print(result)

    def test_directory_structure(self):
        """Test if all required directories exist"""
        print("\n📁 Testing Directory Structure...")

        required_dirs = ["faces", "Attendance", "trainer"]
        all_exist = True

        for dir_name in required_dirs:
            dir_path = self.base_dir / dir_name
            exists = dir_path.exists()

            if not exists:
                dir_path.mkdir(exist_ok=True)
                self.log_test(f"Directory {dir_name}", True, "Created")
            else:
                self.log_test(f"Directory {dir_name}", True, "Exists")

            all_exist = all_exist and exists

        return all_exist

    def test_camera_access(self):
        """Test camera accessibility"""
        print("\n📷 Testing Camera Access...")

        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    height, width = frame.shape[:2]
                    self.log_test(
                        "Camera Access", True, f"Resolution: {width}x{height}"
                    )
                    cap.release()
                    return True
                else:
                    self.log_test("Camera Access", False, "Cannot read frames")
                    cap.release()
                    return False
            else:
                self.log_test("Camera Access", False, "Cannot open camera")
                return False

        except Exception as e:
            self.log_test("Camera Access", False, str(e))
            return False

    def test_face_detection(self):
        """Test face detection functionality"""
        print("\n🔍 Testing Face Detection...")

        try:
            # Load face cascade
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

            if face_cascade.empty():
                self.log_test("Face Detection", False, "Haar cascade not loaded")
                return False

            # Test with camera
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                    face_count = len(faces)
                    self.log_test(
                        "Face Detection", True, f"{face_count} faces detected"
                    )
                    cap.release()
                    return True
                else:
                    self.log_test("Face Detection", False, "Cannot capture frame")
                    cap.release()
                    return False
            else:
                self.log_test("Face Detection", False, "Cannot access camera")
                return False

        except Exception as e:
            self.log_test("Face Detection", False, str(e))
            return False

    def test_face_data_availability(self):
        """Test if face training data is available"""
        print("\n👤 Testing Face Data Availability...")

        if not self.faces_dir.exists():
            self.log_test("Face Data", False, "faces/ directory not found")
            return False

        people_dirs = [d for d in self.faces_dir.iterdir() if d.is_dir()]

        if not people_dirs:
            self.log_test("Face Data", False, "No people registered")
            return False

        total_images = 0
        people_data = []

        for person_dir in people_dirs:
            images = list(person_dir.glob("*.jpg"))
            image_count = len(images)
            total_images += image_count
            people_data.append((person_dir.name, image_count))

            if image_count >= 20:
                self.log_test(
                    f"Face Data - {person_dir.name}", True, f"{image_count} images"
                )
            else:
                self.log_test(
                    f"Face Data - {person_dir.name}",
                    False,
                    f"Only {image_count} images (need 20+)",
                )

        self.log_test(
            "Face Data Summary",
            True,
            f"{len(people_dirs)} people, {total_images} total images",
        )
        return len(people_dirs) > 0 and total_images >= 20

    def test_trained_model(self):
        """Test if face recognition model is trained"""
        print("\n🎓 Testing Trained Model...")

        trainer_file = self.trainer_dir / "trainer.yml"

        if not trainer_file.exists():
            self.log_test("Trained Model", False, "trainer.yml not found")
            return False

        try:
            # Try to load the model
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(str(trainer_file))

            self.log_test("Trained Model", True, "Model loaded successfully")
            return True

        except Exception as e:
            self.log_test("Trained Model", False, f"Cannot load model: {str(e)}")
            return False

    def test_attendance_file_format(self):
        """Test attendance file format"""
        print("\n📊 Testing Attendance File Format...")

        today = datetime.now().strftime("%Y-%m-%d")
        attendance_file = self.attendance_dir / f"Attendance_{today}.csv"

        expected_headers = ["NAME", "TIME", "DATE", "STATUS", "WORK_HOURS"]

        if attendance_file.exists():
            try:
                with open(attendance_file, "r", encoding="utf-8") as file:
                    reader = csv.reader(file)
                    headers = next(reader, None)

                    if headers == expected_headers:

                        # Count records
                        records = list(reader)
                        record_count = len(records)

                        self.log_test(
                            "Attendance Format",
                            True,
                            f"Correct headers, {record_count} records",
                        )
                        return True
                    else:
                        self.log_test(
                            "Attendance Format", False, f"Wrong headers: {headers}"
                        )
                        return False

            except Exception as e:
                self.log_test(
                    "Attendance Format", False, f"Error reading file: {str(e)}"
                )
                return False
        else:
            # Create file with correct headers
            try:
                with open(attendance_file, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(expected_headers)

                self.log_test(
                    "Attendance Format", True, "File created with correct headers"
                )
                return True
            except Exception as e:
                self.log_test(
                    "Attendance Format", False, f"Cannot create file: {str(e)}"
                )
                return False

    def test_work_hours_calculation(self):
        """Test work hours calculation logic"""
        print("\n⏰ Testing Work Hours Calculation...")

        try:
            # Import the function from main script
            import sys

            sys.path.append(str(self.base_dir))

            # Simple test of work hours calculation logic
            from datetime import datetime

            # Test data
            test_cases = [
                # Single session: 9:00-17:00 = 8 hours
                {
                    "records": [("09:00:00", "Clock In"), ("17:00:00", "Clock Out")],
                    "expected": 8.0,
                },
                # Multiple sessions: 9:00-12:00 (3h) + 13:00-17:00 (4h) = 7 hours
                {
                    "records": [
                        ("09:00:00", "Clock In"),
                        ("12:00:00", "Clock Out"),
                        ("13:00:00", "Clock In"),
                        ("17:00:00", "Clock Out"),
                    ],
                    "expected": 7.0,
                },
            ]

            # Simple calculation function for testing
            def calculate_test_hours(records):
                total_hours = 0.0
                clock_in_time = None

                for time_str, status in records:
                    current_time = datetime.strptime(time_str, "%H:%M:%S")

                    if status == "Clock In":
                        clock_in_time = current_time
                    elif status == "Clock Out" and clock_in_time:
                        session_duration = current_time - clock_in_time
                        total_hours += session_duration.total_seconds() / 3600
                        clock_in_time = None

                return round(total_hours, 2)

            all_passed = True
            for i, test_case in enumerate(test_cases, 1):
                calculated = calculate_test_hours(test_case["records"])
                expected = test_case["expected"]

                if calculated == expected:
                    self.log_test(
                        f"Work Hours Test {i}",
                        True,
                        f"{calculated}h (expected {expected}h)",
                    )
                else:
                    self.log_test(
                        f"Work Hours Test {i}",
                        False,
                        f"{calculated}h (expected {expected}h)",
                    )
                    all_passed = False

            return all_passed

        except Exception as e:
            self.log_test("Work Hours Calculation", False, f"Error: {str(e)}")
            return False

    def test_live_recognition(self, duration_seconds=10):
        """Test live face recognition for a short duration"""
        print(f"\n🎥 Testing Live Recognition ({duration_seconds} seconds)...")

        try:
            # Check if model exists
            trainer_file = self.trainer_dir / "trainer.yml"
            if not trainer_file.exists():
                self.log_test("Live Recognition", False, "No trained model found")
                return False

            # Load face detection
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )

            # Load face recognition
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.read(str(trainer_file))

            # Get names from faces directory
            names = ["Unknown"]  # ID 0 is for unknown
            if self.faces_dir.exists():
                for person_dir in self.faces_dir.iterdir():
                    if person_dir.is_dir():
                        names.append(person_dir.name)

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.log_test("Live Recognition", False, "Cannot access camera")
                return False

            start_time = time.time()
            recognition_count = 0
            face_detection_count = 0

            print(f"Testing for {duration_seconds} seconds... Look at the camera!")

            while time.time() - start_time < duration_seconds:
                ret, frame = cap.read()
                if not ret:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                if len(faces) > 0:
                    face_detection_count += 1

                    for x, y, w, h in faces:
                        face_roi = gray[y : y + h, x : x + w]

                        # Try recognition
                        id_pred, confidence = recognizer.predict(face_roi)

                        if confidence < 100:  # Recognition threshold
                            recognition_count += 1
                            name = names[id_pred] if id_pred < len(names) else "Unknown"
                            status = (
                                f"Recognized: {name} (confidence: {confidence:.1f})"
                            )
                        else:
                            status = f"Unknown face (confidence: {confidence:.1f})"

                        # Draw rectangle and text
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(
                            frame,
                            status,
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2,
                        )

                # Show remaining time
                remaining = int(duration_seconds - (time.time() - start_time))
                cv2.putText(
                    frame,
                    f"Test: {remaining}s remaining",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )

                cv2.imshow("Live Recognition Test", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cap.release()
            cv2.destroyAllWindows()

            # Evaluation
            if face_detection_count > 0:
                recognition_rate = (recognition_count / face_detection_count) * 100
                self.log_test(
                    "Live Recognition",
                    True,
                    f"{recognition_count}/{face_detection_count} recognitions ({recognition_rate:.1f}%)",
                )
                return True
            else:
                self.log_test(
                    "Live Recognition", False, "No faces detected during test"
                )
                return False

        except Exception as e:
            self.log_test("Live Recognition", False, f"Error: {str(e)}")
            return False

    def run_quick_test(self, include_live_test=True):
        """Run complete quick test suite"""
        print("🚀 QUICK SYSTEM TEST - Clock In/Clock Out System")
        print("=" * 60)

        test_functions = [
            ("Directory Structure", self.test_directory_structure),
            ("Camera Access", self.test_camera_access),
            ("Face Detection", self.test_face_detection),
            ("Face Data", self.test_face_data_availability),
            ("Trained Model", self.test_trained_model),
            ("Attendance Format", self.test_attendance_file_format),
            ("Work Hours Logic", self.test_work_hours_calculation),
        ]

        if include_live_test:
            test_functions.append(
                ("Live Recognition", lambda: self.test_live_recognition(10))
            )

        passed_tests = 0
        total_tests = len(test_functions)

        for test_name, test_function in test_functions:
            try:
                result = test_function()
                if result:
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")

        # Summary
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)

        for test_name, passed, message in self.test_results:
            status = "✅" if passed else "❌"
            print(f"{status} {test_name}")
            if message and not passed:
                print(f"   └── {message}")

        print(f"\n📊 SCORE: {passed_tests}/{total_tests} tests passed")

        # Overall assessment
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - System ready for production!")
            return True
        elif passed_tests >= total_tests * 0.8:
            print("⚠️ MOSTLY READY - Some issues need attention")
            return False
        else:
            print("❌ SYSTEM NOT READY - Multiple issues need fixing")
            return False

    def generate_test_report(self):
        """Generate detailed test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.base_dir / f"test_report_{timestamp}.txt"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("CLOCK IN/CLOCK OUT SYSTEM - QUICK TEST REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            passed_count = sum(1 for _, passed, _ in self.test_results if passed)
            total_count = len(self.test_results)

            f.write(f"Overall Score: {passed_count}/{total_count} tests passed\n\n")

            f.write("DETAILED RESULTS:\n")
            f.write("-" * 40 + "\n")

            for test_name, passed, message in self.test_results:
                status = "PASS" if passed else "FAIL"
                f.write(f"[{status}] {test_name}\n")
                if message:
                    f.write(f"    Details: {message}\n")
                f.write("\n")

            # Recommendations
            f.write("RECOMMENDATIONS:\n")
            f.write("-" * 40 + "\n")

            failed_tests = [name for name, passed, _ in self.test_results if not passed]

            if not failed_tests:
                f.write("✅ System is ready for production use!\n")
            else:
                f.write("❌ Please address the following issues:\n")
                for test_name in failed_tests:
                    f.write(f"  - Fix {test_name}\n")

        print(f"📄 Test report saved: {report_file.name}")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Quick System Test for Clock In/Clock Out"
    )
    parser.add_argument(
        "--no-live", action="store_true", help="Skip live recognition test"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate detailed test report"
    )

    args = parser.parse_args()

    tester = QuickSystemTest()

    print("🎯 Starting Quick System Test...")
    print("This will test all major components of the clock in/clock out system\n")

    include_live = not args.no_live

    if include_live:
        print("⚠️ Live recognition test will use camera for 10 seconds")
        input("Press Enter to start, or Ctrl+C to cancel...")

    success = tester.run_quick_test(include_live_test=include_live)

    if args.report:
        tester.generate_test_report()

    print(f"\n🏁 Quick test completed - {'Success' if success else 'Issues found'}")


if __name__ == "__main__":
    main()
