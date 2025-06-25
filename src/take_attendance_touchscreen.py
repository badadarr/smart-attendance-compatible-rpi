import cv2
import pickle
import os
import csv
import time
import sys
from datetime import datetime
from pathlib import Path

# Handle NumPy import with error handling for Raspberry Pi
try:
    import numpy as np
except ImportError as e:
    print("❌ NumPy import error:", str(e))
    print("💡 Try running: scripts/troubleshooting/fix_rpi_installation.sh")
    print("💡 Or manually: pip uninstall numpy -y && pip install numpy==1.24.3")
    sys.exit(1)

# Handle scikit-learn import
try:
    from sklearn.neighbors import KNeighborsClassifier
except ImportError as e:
    print("❌ Scikit-learn import error:", str(e))
    print("💡 Try running: scripts/troubleshooting/fix_rpi_installation.sh")
    sys.exit(1)

# Try to import speech synthesis (optional)
try:
    import pyttsx3

    SPEECH_AVAILABLE = True
    print("🔊 Text-to-speech available")
except ImportError:
    SPEECH_AVAILABLE = False
    print("🔇 Text-to-speech not available (install pyttsx3 for speech feedback)")


class TouchscreenAttendanceSystem:
    def __init__(self):
        # Paths
        self.base_dir = Path(__file__).parent.parent  # Go up to project root
        self.data_dir = self.base_dir / "data"
        self.attendance_dir = self.base_dir / "Attendance"
        self.log_dir = self.base_dir / "logs"  # Added for consistency

        # Create directories
        self.attendance_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)  # Ensure log directory exists

        # File paths
        self.names_file = self.data_dir / "names.pkl"
        self.faces_file = self.data_dir / "faces_data.pkl"

        # Initialize components
        self.video = None
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.knn = None
        self.labels = None

        # Speech synthesis
        self.tts_engine = None
        if SPEECH_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 150)  # Speed
                self.tts_engine.setProperty("volume", 0.8)  # Volume
            except:
                self.tts_engine = None
                print("⚠️  Could not initialize text-to-speech")
        self.csv_columns = [
            "NAME",
            "TIME",
            "DATE",
            "STATUS",
            "WORK_HOURS",
            "CONFIDENCE",
            "QUALITY",
            "FLAGS",
        ]  # Updated with enhanced columns

        # Clock in/out settings (these could be externalized to a config file)
        self.clock_in_time = "09:00"
        self.clock_out_time = "17:00"
        self.lunch_break_start = "12:00"
        self.lunch_break_end = "13:00"
        self.max_work_hours = 8.0

        # Recognition settings
        self.confidence_threshold = 0.6
        self.recognition_cooldown = 3  # seconds between recognitions
        self.last_recognition_time = {}
        self.current_recognition_data = None  # Store current recognition data

        # Touchscreen UI variables
        self.button_clicked = False
        self.exit_clicked = False
        self.auto_record_mode = False
        self.last_auto_record = {}
        self.auto_record_cooldown = 5  # seconds for auto recording

        # Enhanced security and anti-fraud settings
        self.min_face_quality = 0.75  # Minimum face quality score
        self.min_consecutive_detections = (
            3  # Require multiple detections (not fully implemented in run_attendance)
        )
        self.max_daily_records = 10  # Maximum records per person per day
        self.suspicious_interval = 30  # Seconds between suspicious rapid entries
        self.face_area_threshold = 0.02  # Minimum face area relative to frame

        # Anti-fraud tracking
        self.detection_history = (
            {}
        )  # Track consecutive detections (not fully implemented in run_attendance)
        self.daily_record_count = {}  # Track daily records per person
        self.last_record_time = {}  # Track last record time per person
        self.suspicious_activities = []  # Log suspicious activities

        # Enhanced recognition settings
        self.recognition_stability_threshold = 5  # Frames of consistent recognition
        self.min_face_distance = 100  # Minimum pixels between face center and previous (not directly used but good to keep)
        self.face_tracking = {}  # Track face positions for stability

    def speak(self, text):
        """Text-to-speech feedback"""
        print(f"🔊 {text}")
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"⚠️  Speech synthesis failed: {e}")  # Log speech errors
                pass  # Fail silently if speech doesn't work

    def load_training_data(self):
        """Load trained face data"""
        if not self.names_file.exists() or not self.faces_file.exists():
            print("❌ Training data not found!")
            print("💡 Please run 'python add_faces_rpi.py' first to register faces")
            return False

        try:
            with open(self.names_file, "rb") as f:
                self.labels = pickle.load(f)

            with open(self.faces_file, "rb") as f:
                faces_data = pickle.load(f)

            # Train KNN classifier
            self.knn = KNeighborsClassifier(n_neighbors=5)
            self.knn.fit(faces_data, self.labels)

            print(f"✅ Training data loaded successfully")
            print(f"📊 Registered faces: {len(set(self.labels))}")
            return True

        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            return False

    def initialize_camera(self):
        """Initialize camera for Raspberry Pi"""
        try:
            # Try different camera indices
            for camera_idx in [0, 1, 2]:
                self.video = cv2.VideoCapture(camera_idx)
                if self.video.isOpened():
                    print(f"📹 Camera initialized on index {camera_idx}")
                    break
            else:
                raise Exception("No camera found")

            # Set camera properties for Raspberry Pi optimization (5 inch display)
            self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.video.set(cv2.CAP_PROP_FPS, 15)
            self.video.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Warm up camera
            for _ in range(10):
                ret, frame = self.video.read()
                if not ret:
                    raise Exception("Camera not responding")

            return True

        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            return False

    def get_current_status(self, name, date):
        """Check current attendance status"""
        attendance_file = self.attendance_dir / f"Attendance_{date}.csv"

        if not attendance_file.exists():
            return None

        try:
            with open(attendance_file, "r") as f:
                reader = csv.DictReader(f)
                records = [row for row in reader if row["NAME"] == name]
                return records[-1]["STATUS"] if records else None
        except Exception as e:
            print(f"⚠️ Error reading current status: {e}")
            return None

    def get_all_records_today(self, name, date):
        """Get all attendance records for a person today"""
        attendance_file = self.attendance_dir / f"Attendance_{date}.csv"

        if not attendance_file.exists():
            return []

        try:
            with open(attendance_file, "r") as f:
                reader = csv.DictReader(f)
                return [row for row in reader if row["NAME"] == name]
        except Exception as e:
            print(f"⚠️ Error reading all records today: {e}")
            return []

    def determine_attendance_status(self, name, current_time, date):
        """Determine if this should be Clock In or Clock Out"""
        records = self.get_all_records_today(name, date)

        if not records:
            return "Clock In"

        last_status = records[-1]["STATUS"]

        if last_status == "Clock In":
            return "Clock Out"
        elif (
            last_status == "Clock Out" or last_status == "Present"
        ):  # "Present" for backward compatibility
            return "Clock In"

        return "Clock In"  # Default to Clock In if status is unknown or first entry

    def calculate_work_hours(self, records):
        """Calculate total work hours from attendance records"""
        if len(records) < 2:
            return 0.0

        total_hours = 0.0
        clock_in_time = None

        for record in records:
            status = record["STATUS"]
            time_str = record["TIME"]

            try:
                record_time = datetime.strptime(time_str, "%H:%M:%S").time()

                if status in ["Clock In", "Present"]:
                    clock_in_time = record_time
                elif status == "Clock Out" and clock_in_time:
                    clock_in_datetime = datetime.combine(
                        datetime.today(), clock_in_time
                    )
                    clock_out_datetime = datetime.combine(datetime.today(), record_time)

                    hours_worked = (
                        clock_out_datetime - clock_in_datetime
                    ).total_seconds() / 3600
                    total_hours += hours_worked
                    clock_in_time = None  # Reset for next Clock In/Out pair

            except ValueError:
                print(f"⚠️  Invalid time format in record: {time_str}")
                continue

        return round(total_hours, 2)

    def format_work_hours(self, hours):
        """Format work hours as HH:MM"""
        if hours <= 0:
            return "00:00"

        hours_int = int(hours)
        minutes = int((hours - hours_int) * 60)
        return f"{hours_int:02d}:{minutes:02d}"

    def recognize_face(self, face_roi):
        """Recognize face using KNN classifier"""
        try:
            resized_face = cv2.resize(face_roi, (50, 50))
            face_flattened = resized_face.flatten().reshape(1, -1)

            expected_features = 50 * 50 * 3  # 7500 for color images
            if face_flattened.shape[1] != expected_features:
                print(
                    f"⚠️ Warning: Feature size mismatch: {face_flattened.shape[1]} vs expected {expected_features}"
                )
                # Attempt to convert to grayscale if feature mismatch
                if resized_face.ndim == 3 and resized_face.shape[2] == 3:
                    gray_resized_face = cv2.cvtColor(resized_face, cv2.COLOR_BGR2GRAY)
                    face_flattened = gray_resized_face.flatten().reshape(1, -1)
                    expected_features = 50 * 50  # 2500 for grayscale
                    if face_flattened.shape[1] != expected_features:
                        print(
                            f"⚠️ Still mismatch after grayscale conversion: {face_flattened.shape[1]} vs expected {expected_features}"
                        )
                        return None, 0.0
                else:
                    return None, 0.0

            prediction = self.knn.predict(face_flattened)[0]
            probabilities = self.knn.predict_proba(face_flattened)[0]
            confidence = max(probabilities)

            return (
                prediction,
                confidence if confidence >= self.confidence_threshold else None,
                confidence,
            )

        except Exception as e:
            print(f"❌ Face recognition error: {e}")
            return None, 0.0

    def can_process_recognition(self, name):
        """Check if enough time has passed since last recognition for a specific person"""
        current_time = time.time()
        last_time = self.last_recognition_time.get(name, 0)

        if current_time - last_time >= self.recognition_cooldown:
            self.last_recognition_time[name] = current_time
            return True
        return False

    def can_auto_record(self, name):
        """Check if enough time has passed since last auto recording for a specific person"""
        current_time = time.time()
        last_time = self.last_auto_record.get(name, 0)
        if current_time - last_time >= self.auto_record_cooldown:
            self.last_auto_record[name] = current_time
            return True
        return False

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse/touch events for 5 inch display"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Record button area
            if 30 <= x <= 180 and 425 <= y <= 465:
                self.button_clicked = True
                print("👆 Record button clicked!")
            # Exit button area
            elif 620 <= x <= 770 and 425 <= y <= 465:
                self.exit_clicked = True
                print("👆 Exit button clicked!")
            # Auto Mode toggle area
            elif 310 <= x <= 490 and 425 <= y <= 465:
                self.auto_record_mode = not self.auto_record_mode
                status = "ON" if self.auto_record_mode else "OFF"
                print(f"👆 Auto Record Mode: {status}")

    def _draw_button(
        self, frame, x1, y1, x2, y2, color, text, font_scale=0.7, thickness=2
    ):
        """Helper to draw a generic button"""
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
        text_size = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
        )[0]
        text_x = x1 + (x2 - x1 - text_size[0]) // 2
        text_y = y1 + (y2 - y1 + text_size[1]) // 2
        cv2.putText(
            frame,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            thickness,
        )

    def _draw_status_info(self, frame, recognized_name):
        """Helper to draw status information including name, next status, and work hours"""
        status_y = 25
        if recognized_name:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time_str = datetime.now().strftime("%H:%M:%S")

            records = self.get_all_records_today(recognized_name, current_date)
            work_hours = self.calculate_work_hours(records)
            work_hours_formatted = self.format_work_hours(work_hours)
            next_status = self.determine_attendance_status(
                recognized_name, current_time_str, current_date
            )

            mode_text = "Auto Mode" if self.auto_record_mode else "Ready"
            status_text = f"{mode_text}: {recognized_name} - Next: {next_status}"
            cv2.putText(
                frame,
                status_text,
                (30, status_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0) if self.auto_record_mode else (0, 255, 255),
                2,
            )

            work_hours_text = f"Today's Hours: {work_hours_formatted}"
            cv2.putText(
                frame,
                work_hours_text,
                (30, status_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

            if records:
                last_record = records[-1]
                last_status_text = (
                    f"Last: {last_record['STATUS']} at {last_record['TIME']}"
                )
                cv2.putText(
                    frame,
                    last_status_text,
                    (400, status_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (200, 200, 200),
                    1,
                )
        else:
            cv2.putText(
                frame,
                "No face recognized",
                (30, status_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
            )

    def _draw_instructions(self, frame):
        """Helper to draw instructions on the screen"""
        instructions = [
            "Clock In/Out Attendance System",
            "Touch RECORD for Clock In/Out",
            "Touch AUTO for automatic mode",
            "System calculates work hours",
        ]
        for i, instruction in enumerate(instructions):
            y_pos = 55 + (i * 20)
            cv2.putText(
                frame,
                instruction,
                (30, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

    def draw_touchscreen_ui(self, frame, recognized_name=None):
        """Draw touchscreen-friendly UI elements optimized for 5 inch display"""
        height, width = frame.shape[:2]
        button_height = 40
        button_y = height - 55

        # Record Attendance Button
        self._draw_button(
            frame, 30, button_y, 180, button_y + button_height, (0, 200, 0), "RECORD"
        )

        # Exit Button
        self._draw_button(
            frame,
            width - 180,
            button_y,
            width - 30,
            button_y + button_height,
            (0, 0, 200),
            "EXIT",
        )

        # Auto Mode Toggle Button
        auto_color = (200, 100, 0) if self.auto_record_mode else (100, 100, 100)
        center_x = width // 2
        self._draw_button(
            frame,
            center_x - 90,
            button_y,
            center_x + 90,
            button_y + button_height,
            auto_color,
            f"AUTO: {'ON' if self.auto_record_mode else 'OFF'}",
            font_scale=0.8,
        )

        # Status display
        self._draw_status_info(frame, recognized_name)

        # Instructions
        self._draw_instructions(frame)

        return frame

    def run_attendance(self):
        """Main attendance recognition loop for touchscreen"""
        print("🎯 Touchscreen Face Recognition Attendance System")
        print("=" * 60)
        print("📱 Instructions:")
        print("   - Touch RECORD button to save attendance")
        print("   - Touch AUTO button to enable automatic recording")
        print("   - Touch EXIT button to quit")
        print("   - Look directly at the camera")
        print("=" * 60)

        cv2.namedWindow("Touchscreen Attendance System", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(
            "Touchscreen Attendance System",
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN,
        )
        cv2.setMouseCallback("Touchscreen Attendance System", self.mouse_callback)

        while True:
            ret, frame = self.video.read()
            if not ret:
                print("❌ Error reading from camera")
                break

            frame = cv2.resize(frame, (800, 480))  # Resize for 5 inch display

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,
                minNeighbors=3,
                minSize=(20, 20),
                maxSize=(300, 300),
            )

            recognized_name = None
            current_frame_faces_data = (
                []
            )  # To store data for faces detected in this frame

            for x, y, w, h in faces:
                frame_area = frame.shape[0] * frame.shape[1]
                face_area = w * h
                face_area_ratio = face_area / frame_area

                if face_area_ratio < self.face_area_threshold:
                    continue

                face_roi = frame[y : y + h, x : x + w]
                quality_score = self.calculate_face_quality(face_roi, face_area_ratio)

                # Check min_face_quality before attempting recognition
                if quality_score < self.min_face_quality:
                    cv2.rectangle(
                        frame, (x, y), (x + w, y + h), (0, 0, 255), 2
                    )  # Red for low quality
                    cv2.putText(
                        frame,
                        "Low Quality",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )
                    continue

                name, confidence = self.recognize_face(face_roi)

                if name is not None:
                    face_center = (x + w // 2, y + h // 2)

                    if self.is_face_stable(name, face_center, confidence):
                        recognized_name = name  # Set recognized_name for UI display

                        current_time_str = datetime.now().strftime("%H:%M:%S")
                        current_date_str = datetime.now().strftime("%Y-%m-%d")
                        attendance_status = self.determine_attendance_status(
                            name, current_time_str, current_date_str
                        )

                        # Store data for the single most stable recognized face in this frame
                        self.current_recognition_data = {
                            "name": name,
                            "time": current_time_str,
                            "date": current_date_str,
                            "status": attendance_status,
                            "confidence": confidence,
                            "quality_score": quality_score,
                        }

                        # Draw enhanced rectangle and labels
                        color = (
                            (0, 255, 0)
                            if quality_score >= 0.8
                            else (
                                (0, 255, 255) if quality_score >= 0.6 else (0, 165, 255)
                            )
                        )
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

                        cv2.putText(
                            frame,
                            name,
                            (x, y - 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            color,
                            2,
                        )
                        cv2.putText(
                            frame,
                            f"{confidence*100:.1f}%",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            color,
                            2,
                        )
                        cv2.putText(
                            frame,
                            f"Q:{quality_score:.2f}",
                            (x + w - 60, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color,
                            2,
                        )
                        cv2.putText(
                            frame,
                            f"Next: {attendance_status}",
                            (x, y + h + 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 255, 0),
                            2,
                        )

                        # Auto record logic
                        if self.auto_record_mode and self.can_auto_record(name):
                            if self.enhanced_save_attendance(
                                name,
                                current_time_str,
                                current_date_str,
                                attendance_status,
                                confidence,
                                quality_score,
                            ):
                                message = f"Auto recorded: {name} - {attendance_status}"
                                self.speak(message)
                                print(f"🤖 {message}")
                                cv2.putText(
                                    frame,
                                    "AUTO RECORDED!",
                                    (x, y + h + 40),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.8,
                                    (0, 255, 0),
                                    2,
                                )
                                # Brief pause for visual feedback
                                cv2.imshow("Touchscreen Attendance System", frame)
                                cv2.waitKey(500)  # Show "AUTO RECORDED!" for 0.5 second
                    else:
                        cv2.rectangle(
                            frame, (x, y), (x + w, y + h), (0, 100, 255), 2
                        )  # Orange for stabilizing
                        cv2.putText(
                            frame,
                            f"{name} (Stabilizing...)",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 100, 255),
                            2,
                        )
                else:
                    cv2.rectangle(
                        frame, (x, y), (x + w, y + h), (0, 0, 255), 2
                    )  # Red for unknown
                    cv2.putText(
                        frame,
                        "Unknown",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )

            # If no faces were recognized or stable in this frame, clear current_recognition_data
            if not recognized_name:
                self.current_recognition_data = None

            frame = self.draw_touchscreen_ui(frame, recognized_name)
            cv2.imshow("Touchscreen Attendance System", frame)

            # Handle button clicks
            if self.button_clicked:
                self.button_clicked = False
                if self.current_recognition_data:
                    data = self.current_recognition_data
                    if self.can_process_recognition(data["name"]):
                        if self.enhanced_save_attendance(
                            data["name"],
                            data["time"],
                            data["date"],
                            data["status"],
                            data["confidence"],
                            data["quality_score"],
                        ):
                            message = f"Attendance recorded: {data['name']} - {data['status']}"
                            self.speak(message)
                            print(f"✅ {message}")
                            cv2.putText(
                                frame,
                                "RECORDED!",
                                (300, 240),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                1.5,
                                (0, 255, 0),
                                3,
                            )
                            cv2.imshow("Touchscreen Attendance System", frame)
                            cv2.waitKey(1000)
                        else:
                            print("❌ Failed to save attendance - validation failed")
                            self.speak("Attendance failed - please try again")
                    else:
                        print(
                            f"⏳ Please wait before recording again for {data['name']}"
                        )
                else:
                    print("👤 No face recognized to record attendance")

            if self.exit_clicked:
                break

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break

        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.video:
            self.video.release()
        cv2.destroyAllWindows()
        print("🧹 Resources cleaned up")

    def run(self):
        """Main execution method"""
        try:
            if not self.load_training_data():
                return False
            if not self.initialize_camera():
                return False
            self.run_attendance()
            return True
        except KeyboardInterrupt:
            print("\n⚠️  System stopped by user")
            self.cleanup()
            return True
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            self.cleanup()
            return False

    def calculate_face_quality(self, face_roi, face_area_ratio):
        """Calculate face quality score based on multiple factors"""
        try:
            if face_roi is None or face_roi.size == 0:
                return 0.0

            area_score = min(face_area_ratio / self.face_area_threshold, 1.0)

            # Convert to grayscale for sharpness, brightness, and symmetry
            if face_roi.ndim == 3 and face_roi.shape[2] == 3:
                gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            elif face_roi.ndim == 2:
                gray_face = face_roi
            else:
                return 0.0  # Unsupported format

            if (
                gray_face.shape[0] < 2 or gray_face.shape[1] < 2
            ):  # Ensure minimum size for Laplacian
                return 0.0

            laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 500.0, 1.0)

            mean_brightness = np.mean(gray_face)
            brightness_score = 1.0 - abs(mean_brightness - 127) / 127

            height, width = gray_face.shape
            if width < 2:  # Ensure width for symmetry
                return 0.0

            left_half = gray_face[:, : width // 2]
            right_half = cv2.flip(gray_face[:, width // 2 :], 1)
            min_width = min(left_half.shape[1], right_half.shape[1])
            if min_width == 0:  # Handle cases where one half is empty
                symmetry_score = 0.0
            else:
                left_half = left_half[:, :min_width]
                right_half = right_half[:, :min_width]
                symmetry_score = 1.0 - (np.mean(np.abs(left_half - right_half)) / 255.0)

            quality_score = (
                area_score * 0.3
                + sharpness_score * 0.4
                + brightness_score * 0.2
                + symmetry_score * 0.1
            )
            return quality_score

        except Exception as e:
            print(f"⚠️ Error calculating face quality: {e}")
            return 0.0

    def is_face_stable(self, name, face_center, confidence):
        """Check if face detection is stable across multiple frames"""
        current_time = time.time()

        if name not in self.face_tracking:
            self.face_tracking[name] = {
                "positions": [],
                "confidences": [],
                "first_detection": current_time,
                "stable_count": 0,
            }

        tracking = self.face_tracking[name]

        # Add current detection
        tracking["positions"].append(face_center)
        tracking["confidences"].append(confidence)

        # Keep only recent detections (last 10 frames)
        if len(tracking["positions"]) > 10:
            tracking["positions"].pop(0)
            tracking["confidences"].pop(0)

        # Reset stable count if not enough positions
        if len(tracking["positions"]) < self.recognition_stability_threshold:
            tracking["stable_count"] = 0
            return False

        # Calculate stability criteria
        positions = np.array(tracking["positions"])
        pos_variance = np.var(positions, axis=0)
        position_stable = np.all(
            pos_variance < 100
        )  # Low position variance (pixels squared)

        conf_variance = np.var(tracking["confidences"])
        confidence_stable = conf_variance < 0.05  # Low confidence variance

        time_elapsed = current_time - tracking["first_detection"]
        time_sufficient = time_elapsed >= 2.0  # At least 2 seconds

        if position_stable and confidence_stable and time_sufficient:
            tracking["stable_count"] += 1
            return (
                tracking["stable_count"] >= self.min_consecutive_detections
            )  # Use min_consecutive_detections here
        else:
            tracking["stable_count"] = 0  # Reset if not stable
            return False

    def check_suspicious_activity(self, name):
        """Detect suspicious activities that might indicate fraud"""
        current_time = time.time()
        current_date = datetime.now().strftime("%Y-%m-%d")

        suspicious_flags = []

        # Check 1: Too many records in a day
        daily_key = f"{name}_{current_date}"
        current_count = self.daily_record_count.get(daily_key, 0)

        if current_count >= self.max_daily_records:
            suspicious_flags.append(
                f"Exceeded daily record limit ({current_count}/{self.max_daily_records})"
            )

        # Check 2: Too rapid consecutive entries
        if name in self.last_record_time:
            time_diff = current_time - self.last_record_time[name]
            if time_diff < self.suspicious_interval:
                suspicious_flags.append(
                    f"Rapid entry detected ({time_diff:.1f}s interval)"
                )

        # Check 3: Unusual time patterns (very early/late entries)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Example: outside 6 AM to 10 PM
            suspicious_flags.append(f"Unusual time entry ({current_hour:02d}:xx)")

        # Check 4: Weekend entries (if configured to be suspicious)
        current_weekday = datetime.now().weekday()
        # if current_weekday >= 5: # Saturday = 5, Sunday = 6
        #     suspicious_flags.append("Weekend entry detected")
        # Removed as weekend entries might be valid for some setups. Add if needed.

        return suspicious_flags

    def log_suspicious_activity(self, name, flags, additional_info=None):
        """Log suspicious activities for review"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        activity_log = {
            "timestamp": timestamp,
            "name": name,
            "flags": flags,
            "additional_info": additional_info or {},
        }
        self.suspicious_activities.append(
            activity_log
        )  # Keep in memory for current session

        log_file = (
            self.log_dir
            / f"suspicious_activities_{datetime.now().strftime('%Y-%m')}.log"
        )
        log_file.parent.mkdir(exist_ok=True)  # Ensure log directory exists

        try:
            with open(log_file, "a") as f:
                f.write(
                    f"{timestamp} | {name} | {', '.join(flags)} | {json.dumps(additional_info)}\n"
                )
        except Exception as e:
            print(f"⚠️ Failed to write to log file: {e}")

        print(f"🚨 SUSPICIOUS ACTIVITY DETECTED:")
        print(f"   Name: {name}")
        print(f"   Flags: {', '.join(flags)}")
        print(f"   Time: {timestamp}")
        if additional_info:
            print(f"   Info: {additional_info}")

    def enhanced_save_attendance(
        self, name, timestamp, date, status, confidence, quality_score
    ):
        """Enhanced attendance saving with fraud detection and validation"""

        suspicious_flags = self.check_suspicious_activity(name)

        if suspicious_flags:
            self.log_suspicious_activity(
                name,
                suspicious_flags,
                {
                    "confidence": confidence,
                    "quality_score": quality_score,
                    "status": status,
                },
            )

            # Decision point: Block entry for high-risk activities
            # Example: Block if exceeded daily limit OR multiple suspicious flags
            if (
                "Exceeded daily" in " ".join(suspicious_flags)
                or len(suspicious_flags) >= 2
            ):
                print(f"❌ Attendance blocked due to suspicious activity: {name}")
                self.speak(
                    f"Attendance blocked for {name} - suspicious activity detected"
                )
                return False

        # Quality and Confidence validation (already checked before passing to enhanced_save_attendance, but good to double check)
        if quality_score < self.min_face_quality:
            print(
                f"❌ Face quality too low for saving: {quality_score:.2f} < {self.min_face_quality}"
            )
            return False

        if confidence < self.confidence_threshold:
            print(
                f"❌ Recognition confidence too low for saving: {confidence:.2f} < {self.confidence_threshold}"
            )
            return False

        attendance_file = self.attendance_dir / f"Attendance_{date}.csv"
        file_exists = attendance_file.exists()

        try:
            # Ensure the CSV columns are always consistent, especially for new files.
            # If the file exists, we need to read it to get existing records.
            # If it's a new file, the columns will be written.

            # Read existing records
            current_records = self.get_all_records_today(name, date)

            # Add the record we're about to save to the list for work hour calculation
            temp_record = {
                "NAME": name,
                "TIME": timestamp,
                "DATE": date,
                "STATUS": status,
            }
            current_records.append(temp_record)

            work_hours = self.calculate_work_hours(current_records)
            work_hours_formatted = self.format_work_hours(work_hours)

            with open(attendance_file, "a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(self.csv_columns)  # Write header if file is new

                flags_str = "|".join(suspicious_flags) if suspicious_flags else ""
                writer.writerow(
                    [
                        name,
                        timestamp,
                        date,
                        status,
                        work_hours_formatted,
                        f"{confidence:.3f}",
                        f"{quality_score:.3f}",
                        flags_str,
                    ]
                )

            # Update tracking counters
            current_time = time.time()
            daily_key = f"{name}_{date}"
            self.daily_record_count[daily_key] = (
                self.daily_record_count.get(daily_key, 0) + 1
            )
            self.last_record_time[name] = current_time

            print(f"✅ Enhanced attendance saved: {name} - {status}")
            print(f"   Confidence: {confidence:.3f}, Quality: {quality_score:.3f}")
            if suspicious_flags:
                print(f"   ⚠️ Flags: {', '.join(suspicious_flags)}")

            return True

        except Exception as e:
            print(f"❌ Error saving enhanced attendance: {e}")
            return False


def main():
    """Main function"""
    try:
        with open("/proc/cpuinfo", "r") as f:
            if "Raspberry Pi" in f.read():
                print("🍓 Running on Raspberry Pi")
            else:
                print("💻 Running on non-Raspberry Pi system")
    except:
        print("💻 System detection unavailable")

    print("🔍 Checking dependencies...")
    missing_deps = []

    try:
        import sklearn

        print("✅ scikit-learn available")
    except ImportError:
        missing_deps.append("scikit-learn")

    try:
        import cv2

        print("✅ OpenCV available")
    except ImportError:
        missing_deps.append("opencv-python")

    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("💡 Install with: pip install " + " ".join(missing_deps))
        return

    system = TouchscreenAttendanceSystem()
    system.run()


if __name__ == "__main__":
    main()
