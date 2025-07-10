import cv2
import pickle
import os
import csv
import time
import sys
import json  # Added for logging suspicious activities
from datetime import datetime
from pathlib import Path

# Try to import quality configuration
try:
    sys.path.append(str(Path(__file__).parent.parent / "config"))
    from quality_config import (
        get_active_threshold,
        get_active_description,
        QUALITY_WEIGHTS,
        SHARPNESS_VARIANCE_THRESHOLD,
    )

    QUALITY_CONFIG_AVAILABLE = True
    print("🔧 Quality configuration loaded")
except ImportError:
    QUALITY_CONFIG_AVAILABLE = False
    print("⚠️  Quality configuration not found, using defaults")

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
            "STATUS",
        ]  # Simplified CSV format

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
        # REMOVED: Strict quality threshold requirement
        # NEW: More flexible quality assessment
        self.enable_quality_check = False  # Disable strict quality checking
        self.min_face_quality = 0.1  # Very low threshold, essentially disabled
        self.quality_info_only = True  # Only show quality info, don't block

        print("📊 Quality checking: DISABLED (flexible mode)")
        print("📝 System will accept faces regardless of calculated quality")

        # Alternative validation methods (replace strict quality) - VERY PERMISSIVE
        self.min_face_size = (20, 20)  # Very small minimum face size
        self.max_face_size = (600, 600)  # Very large maximum face size
        self.min_confidence_for_auto = 0.4  # Low confidence for auto-record
        self.min_confidence_manual = 0.3  # Very low confidence for manual record

        # Enhanced stability checking (replace quality gating) - VERY FLEXIBLE
        self.stability_frames_required = 1  # Only 1 frame required (almost instant)
        self.max_position_variance = 1000  # Very high variance allowed
        self.confidence_consistency_threshold = 0.3  # High confidence variance allowed

        self.min_consecutive_detections = (
            3  # Require multiple detections (not fully implemented in run_attendance)
        )
        self.max_daily_records = 10  # Maximum records per person per day
        self.suspicious_interval = 30  # Seconds between suspicious rapid entries
        # Face area validation (simple but effective) - ULTRA PERMISSIVE
        self.face_area_threshold = 0.001  # Ultra low threshold
        self.optimal_face_area_min = 0.005  # Very small warning threshold
        self.optimal_face_area_max = 0.5  # Very large warning threshold

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
            unique_faces = len(set(self.labels))
            total_samples = len(self.labels)
            print(f"📊 Registered faces: {unique_faces}")
            print(f"📊 Total training samples: {total_samples}")
            print(f"📋 Registered names: {', '.join(sorted(set(self.labels)))}")
            return True

        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            print(f"💡 Try running: python tools/analyze_training_data.py")
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

    # Work hours calculation removed - not needed in simplified format

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
        """Helper to draw status information - simplified"""
        status_y = 25
        if recognized_name:
            current_date = datetime.now().strftime("%Y-%m-%d")
            current_time_str = datetime.now().strftime("%H:%M:%S")

            records = self.get_all_records_today(recognized_name, current_date)
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

            entries_today = len(records)
            entries_text = f"Today's Entries: {entries_today}"
            cv2.putText(
                frame,
                entries_text,
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
        """Helper to draw instructions - UPDATED for flexible mode"""
        instructions = [
            "Clock In/Out Attendance System (Flexible Mode)",
            "Touch RECORD for Clock In/Out",
            "Touch AUTO for automatic mode",
            "System calculates work hours",
            f"Confidence: Auto≥{self.min_confidence_for_auto:.1f}, Manual≥{self.min_confidence_manual:.1f}",
            "Quality checking: DISABLED for flexibility",
        ]
        for i, instruction in enumerate(instructions):
            y_pos = 55 + (i * 20)
            color = (255, 255, 255) if i < 4 else (0, 255, 255)
            cv2.putText(
                frame, instruction, (30, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
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
        """Main attendance recognition loop - MODIFIED for flexible validation"""
        print("🎯 Touchscreen Face Recognition Attendance System (Flexible Mode)")
        print("=" * 60)
        print("📱 Instructions:")
        print("   - Touch RECORD button to save attendance")
        print("   - Touch AUTO button to enable automatic recording")
        print("   - Touch EXIT button to quit")
        print("   - Look directly at the camera")
        print("   - Quality checking is DISABLED for maximum flexibility")
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

            frame = cv2.resize(frame, (800, 480))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,  # More sensitive detection
                minNeighbors=3,  # Reduced for more detections
                minSize=(20, 20),
                maxSize=(400, 400),
            )

            recognized_name = None

            for x, y, w, h in faces:
                face_roi = frame[y : y + h, x : x + w]
                face_rect = (x, y, w, h)

                # Basic validation (replaces strict quality checking)
                validation = self.validate_face_basic(face_roi, face_rect, frame.shape)

                # REMOVED: Quality threshold blocking
                # OLD: if quality_score < self.min_face_quality: continue

                # NEW: Only check basic area threshold (very permissive)
                frame_area = frame.shape[0] * frame.shape[1]
                face_area = w * h
                face_area_ratio = face_area / frame_area

                if face_area_ratio < self.face_area_threshold:
                    continue  # Only skip extremely small faces

                # Attempt face recognition regardless of calculated quality
                recognition_result = self.recognize_face(face_roi)

                if len(recognition_result) == 3:
                    name, confidence, raw_confidence = recognition_result
                else:
                    name, confidence = recognition_result
                    raw_confidence = confidence if confidence else 0.0

                # Calculate quality for display only
                quality_score = self.calculate_face_quality(face_roi, face_area_ratio)

                if name is not None:
                    face_center = (x + w // 2, y + h // 2)

                    # Use enhanced stability checking (but don't require it for recording)
                    is_stable, stability_msg = self.is_face_stable_enhanced(
                        name, face_center, confidence, face_rect
                    )

                    # FLEXIBLE MODE: Accept face even if not fully stable
                    recognized_name = name

                    current_time_str = datetime.now().strftime("%H:%M:%S")
                    current_date_str = datetime.now().strftime("%Y-%m-%d")
                    attendance_status = self.determine_attendance_status(
                        name, current_time_str, current_date_str
                    )

                    # Use different confidence thresholds for auto vs manual
                    min_conf = (
                        self.min_confidence_for_auto
                        if self.auto_record_mode
                        else self.min_confidence_manual
                    )

                    if confidence >= min_conf:
                        self.current_recognition_data = {
                            "name": name,
                            "time": current_time_str,
                            "date": current_date_str,
                            "status": attendance_status,
                            "confidence": confidence,
                            "quality_score": quality_score,
                        }

                        # Draw enhanced rectangle - color based on confidence and warnings
                        if confidence >= 0.8:
                            color = (0, 255, 0)  # Green for high confidence
                        elif confidence >= 0.6:
                            color = (0, 255, 255)  # Yellow for medium confidence
                        else:
                            color = (0, 165, 255)  # Orange for low confidence

                        # Add red tint if there are warnings
                        if validation["warnings"]:
                            color = (0, 100, 255)  # Orange-red for warnings

                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

                        # Display information with stability status
                        stability_indicator = "✓" if is_stable else "~"
                        cv2.putText(
                            frame,
                            f"{stability_indicator} {name}",
                            (x, y - 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            color,
                            2,
                        )
                        cv2.putText(
                            frame,
                            f"Conf: {confidence*100:.1f}%",
                            (x, y - 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            color,
                            2,
                        )
                        cv2.putText(
                            frame,
                            f"Q: {quality_score:.2f} | {stability_msg}",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            color,
                            1,
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

                        # Show validation info
                        if validation["warnings"]:
                            warning_text = validation["warnings"][0][
                                :20
                            ]  # Truncate long warnings
                            cv2.putText(
                                frame,
                                f"⚠️ {warning_text}",
                                (x, y + h + 40),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.4,
                                (0, 165, 255),
                                1,
                            )

                        # Auto record logic
                        if (
                            self.auto_record_mode
                            and self.can_auto_record(name)
                            and confidence >= self.min_confidence_for_auto
                        ):
                            if self.save_attendance(name, current_time_str, attendance_status):
                                message = f"Auto recorded: {name} - {attendance_status}"
                                self.speak(f"Auto recorded: {name} - {attendance_status}")
                                print(f"🤖 {message}")
                    else:
                        # Confidence too low but still show the face
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        stability_indicator = "✓" if is_stable else "~"
                        cv2.putText(
                            frame,
                            f"{stability_indicator} {name} (Low Conf: {confidence*100:.1f}%)",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 0, 255),
                            2,
                        )
                        # Still store recognition data for manual recording
                        self.current_recognition_data = {
                            "name": name,
                            "time": current_time_str,
                            "date": current_date_str,
                            "status": attendance_status,
                            "confidence": confidence,
                            "quality_score": quality_score,
                        }
                else:
                    # Unknown face
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(
                        frame,
                        "Unknown",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )

            # Clear recognition data if no stable face
            if not recognized_name:
                self.current_recognition_data = None

            frame = self.draw_touchscreen_ui(frame, recognized_name)
            cv2.imshow("Touchscreen Attendance System", frame)

            # Handle button clicks with ultra-flexible confidence requirements
            if self.button_clicked:
                self.button_clicked = False
                if self.current_recognition_data:
                    data = self.current_recognition_data
                    if self.can_process_recognition(data["name"]):
                        # Accept manual recording
                        if self.save_attendance(data["name"], data["time"], data["status"]):
                            message = f"Attendance recorded: {data['name']} - {data['status']} (Manual)"
                            self.speak(f"Attendance recorded for {data['name']}")
                            print(f"✅ {message}")
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
        """Calculate face quality score - NOW FOR INFORMATION ONLY"""
        try:
            if face_roi is None or face_roi.size == 0:
                return 0.0

            # Calculate quality but don't use it for blocking
            area_score = min(face_area_ratio / 0.01, 1.0)  # More lenient base

            if face_roi.ndim == 3 and face_roi.shape[2] == 3:
                gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            elif face_roi.ndim == 2:
                gray_face = face_roi
            else:
                return 0.5  # Return neutral score instead of 0

            if gray_face.shape[0] < 2 or gray_face.shape[1] < 2:
                return 0.5  # Return neutral score for small faces

            # Simplified quality calculation
            try:
                laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
                sharpness_score = min(laplacian_var / 300.0, 1.0)  # More lenient
            except:
                sharpness_score = 0.5

            try:
                mean_brightness = np.mean(gray_face)
                brightness_score = 1.0 - abs(mean_brightness - 127) / 127
            except:
                brightness_score = 0.5

            # Simple average, more forgiving
            quality_score = (area_score + sharpness_score + brightness_score) / 3.0
            return max(quality_score, 0.1)  # Ensure minimum score

        except Exception as e:
            print(f"⚠️ Error calculating face quality: {e}")
            return 0.5  # Return neutral score on error

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

    def validate_face_basic(self, face_roi, face_rect, frame_shape):
        """Basic face validation - replaces strict quality checking"""
        x, y, w, h = face_rect
        frame_height, frame_width = frame_shape[:2]

        validation_results = {"valid": True, "warnings": [], "info": []}

        # 1. Size validation
        if w < self.min_face_size[0] or h < self.min_face_size[1]:
            validation_results["warnings"].append(f"Face too small ({w}x{h})")
        elif w > self.max_face_size[0] or h > self.max_face_size[1]:
            validation_results["warnings"].append(f"Face too large ({w}x{h})")
        else:
            validation_results["info"].append(f"Good size ({w}x{h})")

        # 2. Position validation
        if (
            x < 10
            or y < 10
            or (x + w) > (frame_width - 10)
            or (y + h) > (frame_height - 10)
        ):
            validation_results["warnings"].append("Face near edge")
        else:
            validation_results["info"].append("Good position")

        # 3. Area validation
        face_area = w * h
        frame_area = frame_width * frame_height
        area_ratio = face_area / frame_area

        if area_ratio < self.optimal_face_area_min:
            validation_results["warnings"].append(
                f"Face small in frame ({area_ratio:.3f})"
            )
        elif area_ratio > self.optimal_face_area_max:
            validation_results["warnings"].append(
                f"Face large in frame ({area_ratio:.3f})"
            )
        else:
            validation_results["info"].append(f"Good frame ratio ({area_ratio:.3f})")

        # 4. Basic brightness check
        if face_roi is not None and face_roi.size > 0:
            try:
                if face_roi.ndim == 3:
                    gray_face = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
                else:
                    gray_face = face_roi

                mean_brightness = np.mean(gray_face)
                if mean_brightness < 50:
                    validation_results["warnings"].append("Face too dark")
                elif mean_brightness > 200:
                    validation_results["warnings"].append("Face too bright")
                else:
                    validation_results["info"].append(
                        f"Good brightness ({mean_brightness:.0f})"
                    )
            except:
                pass

        return validation_results

    def is_face_stable_enhanced(self, name, face_center, confidence, face_rect):
        """Enhanced face stability checking - replaces quality gating"""
        current_time = time.time()

        if name not in self.face_tracking:
            self.face_tracking[name] = {
                "positions": [],
                "confidences": [],
                "sizes": [],
                "first_detection": current_time,
                "stable_count": 0,
                "last_validation": current_time,
            }

        tracking = self.face_tracking[name]

        # Add current detection
        tracking["positions"].append(face_center)
        tracking["confidences"].append(confidence)
        tracking["sizes"].append((face_rect[2], face_rect[3]))  # w, h

        # Keep recent history
        max_history = 10
        if len(tracking["positions"]) > max_history:
            tracking["positions"] = tracking["positions"][-max_history:]
            tracking["confidences"] = tracking["confidences"][-max_history:]
            tracking["sizes"] = tracking["sizes"][-max_history:]

        # Check if we have enough detections
        if len(tracking["positions"]) < self.stability_frames_required:
            return False, "Collecting samples..."

        # Calculate stability metrics
        positions = np.array(tracking["positions"])
        confidences = np.array(tracking["confidences"])

        # Position stability
        pos_variance = np.var(positions, axis=0)
        position_stable = np.all(pos_variance < self.max_position_variance)

        # Confidence stability
        conf_variance = np.var(confidences)
        confidence_stable = conf_variance < self.confidence_consistency_threshold

        # Time requirement - ULTRA FLEXIBLE
        time_elapsed = current_time - tracking["first_detection"]
        time_sufficient = time_elapsed >= 0.5  # Very short time requirement

        # Overall stability assessment - VERY PERMISSIVE
        if position_stable and confidence_stable and time_sufficient:
            tracking["stable_count"] += 1
            return True, "Stable"  # Immediately stable
        elif time_sufficient:  # If enough time passed, consider it stable enough
            tracking["stable_count"] += 1
            return True, "Flexible"  # Flexible stability
        else:
            tracking["stable_count"] = 0
            return False, f"Wait {0.5-time_elapsed:.1f}s"

    def save_attendance(self, name, time_str, status):
        """Simple attendance saving - NEW FORMAT"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            attendance_file = self.attendance_dir / f"Attendance_{current_date}.csv"

            # Prepare CSV row with simplified columns
            row_data = {
                "NAME": name,
                "TIME": time_str,
                "STATUS": status,
            }

            # Write to CSV
            file_exists = attendance_file.exists()
            with open(attendance_file, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_columns)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row_data)

            print(f"✅ Attendance saved: {name} - {status} at {time_str}")
            return True

        except Exception as e:
            print(f"❌ Error saving attendance: {e}")
            return False

    # Suspicious activity logging removed - not needed in simplified format


def main():
    """Main function - UPDATED messaging"""
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

    print("🎯 FLEXIBLE MODE ENABLED:")
    print("   ✅ Quality checking disabled")
    print("   ✅ Lower confidence thresholds")
    print("   ✅ Enhanced stability checking")
    print("   ✅ Basic face validation only")
    print("   📊 Quality scores shown for information only")

    system.run()


if __name__ == "__main__":
    main()
