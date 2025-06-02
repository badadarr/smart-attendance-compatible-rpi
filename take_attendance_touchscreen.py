import cv2
import pickle
import os
import csv
import time
from datetime import datetime
from pathlib import Path
import sys

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
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.attendance_dir = self.base_dir / "Attendance"

        # Create directories
        self.attendance_dir.mkdir(exist_ok=True)

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

        # CSV columns
        self.csv_columns = ["NAME", "TIME", "DATE", "STATUS"]

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

    def speak(self, text):
        """Text-to-speech feedback"""
        print(f"🔊 {text}")
        if self.tts_engine:
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except:
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

            # Set camera properties for Raspberry Pi optimization
            self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.video.set(cv2.CAP_PROP_FPS, 15)
            self.video.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Warm up camera
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
                statuses = [row["STATUS"] for row in reader if row["NAME"] == name]
                return statuses[-1] if statuses else None
        except:
            return None

    def save_attendance(self, name, timestamp, date, status):
        """Save attendance record"""
        attendance_file = self.attendance_dir / f"Attendance_{date}.csv"
        file_exists = attendance_file.exists()

        try:
            with open(attendance_file, "a", newline="") as f:
                writer = csv.writer(f)

                # Write header if new file
                if not file_exists:
                    writer.writerow(self.csv_columns)

                # Write attendance record
                writer.writerow([name, timestamp, date, status])
                return True

        except Exception as e:
            print(f"❌ Error saving attendance: {e}")
            return False

    def recognize_face(self, face_roi):
        """Recognize face using KNN classifier"""
        try:
            # Prepare face data - resize to 50x50 pixel to match training data
            resized_face = cv2.resize(face_roi, (50, 50))

            # Flatten for KNN input (50x50x3 = 7500 features for color images)
            face_flattened = resized_face.flatten().reshape(1, -1)

            # The training data uses color images (7500 features)
            expected_features = 50 * 50 * 3  # 7500 for color images

            if face_flattened.shape[1] != expected_features:
                print(
                    f"⚠️ Warning: Feature size mismatch: {face_flattened.shape[1]} vs expected {expected_features}"
                )
                return None, 0.0

            # Get prediction and probabilities
            prediction = self.knn.predict(face_flattened)[0]
            probabilities = self.knn.predict_proba(face_flattened)[0]
            confidence = max(probabilities)

            if confidence >= self.confidence_threshold:
                return prediction, confidence
            else:
                return None, confidence

        except Exception as e:
            print(f"❌ Face recognition error: {e}")
            return None, 0.0

    def can_process_recognition(self, name):
        """Check if enough time has passed since last recognition"""
        current_time = time.time()
        last_time = self.last_recognition_time.get(name, 0)

        if current_time - last_time >= self.recognition_cooldown:
            self.last_recognition_time[name] = current_time
            return True

        return False

    def can_auto_record(self, name):
        """Check if enough time has passed since last auto recording"""
        current_time = time.time()
        last_time = self.last_auto_record.get(name, 0)

        if current_time - last_time >= self.auto_record_cooldown:
            self.last_auto_record[name] = current_time
            return True

        return False

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse/touch events"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Check if click is on Record button area (bottom left)
            if 50 <= x <= 250 and 650 <= y <= 700:
                self.button_clicked = True
                print("👆 Record button clicked!")

            # Check if click is on Exit button area (bottom right)
            elif 1030 <= x <= 1230 and 650 <= y <= 700:
                self.exit_clicked = True
                print("👆 Exit button clicked!")

            # Check if click is on Auto Mode toggle (bottom center)
            elif 515 <= x <= 765 and 650 <= y <= 700:
                self.auto_record_mode = not self.auto_record_mode
                status = "ON" if self.auto_record_mode else "OFF"
                print(f"👆 Auto Record Mode: {status}")

    def draw_touchscreen_ui(self, frame, recognized_name=None):
        """Draw touchscreen-friendly UI elements"""
        height, width = frame.shape[:2]

        # Create buttons at the bottom
        button_height = 50
        button_y = height - 70

        # Record Attendance Button (Green)
        cv2.rectangle(
            frame, (50, button_y), (250, button_y + button_height), (0, 200, 0), -1
        )
        cv2.rectangle(
            frame, (50, button_y), (250, button_y + button_height), (255, 255, 255), 2
        )
        cv2.putText(
            frame,
            "RECORD",
            (80, button_y + 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )

        # Exit Button (Red)
        cv2.rectangle(
            frame,
            (width - 250, button_y),
            (width - 50, button_y + button_height),
            (0, 0, 200),
            -1,
        )
        cv2.rectangle(
            frame,
            (width - 250, button_y),
            (width - 50, button_y + button_height),
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            "EXIT",
            (width - 200, button_y + 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )

        # Auto Mode Toggle Button (Blue/Gray)
        auto_color = (200, 100, 0) if self.auto_record_mode else (100, 100, 100)
        center_x = width // 2
        cv2.rectangle(
            frame,
            (center_x - 125, button_y),
            (center_x + 125, button_y + button_height),
            auto_color,
            -1,
        )
        cv2.rectangle(
            frame,
            (center_x - 125, button_y),
            (center_x + 125, button_y + button_height),
            (255, 255, 255),
            2,
        )
        auto_text = "AUTO: ON" if self.auto_record_mode else "AUTO: OFF"
        cv2.putText(
            frame,
            auto_text,
            (center_x - 80, button_y + 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        # Status display
        status_y = 30
        if recognized_name:
            if self.auto_record_mode:
                status_text = f"Auto Mode: {recognized_name} detected"
                cv2.putText(
                    frame,
                    status_text,
                    (50, status_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
            else:
                status_text = f"Ready to record: {recognized_name}"
                cv2.putText(
                    frame,
                    status_text,
                    (50, status_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2,
                )
        else:
            cv2.putText(
                frame,
                "No face recognized",
                (50, status_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

        # Instructions
        instructions = [
            "Touchscreen Attendance System",
            "Touch RECORD button to save attendance",
            "Touch AUTO to enable automatic recording",
            "Touch EXIT to quit",
        ]

        for i, instruction in enumerate(instructions):
            y_pos = 80 + (i * 25)
            cv2.putText(
                frame,
                instruction,
                (50, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
            )

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

        # Set up mouse callback for touch events
        cv2.namedWindow("Touchscreen Attendance System", cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(
            "Touchscreen Attendance System",
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN,
        )
        cv2.setMouseCallback("Touchscreen Attendance System", self.mouse_callback)

        frame_count = 0

        while True:
            ret, frame = self.video.read()
            if not ret:
                print("❌ Error reading from camera")
                break

            frame_count += 1

            # Resize frame to fit screen better
            frame = cv2.resize(frame, (1280, 720))

            # Face detection
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

            # Process detected faces
            for x, y, w, h in faces:
                # Crop face area from original color frame
                face_roi = frame[y : y + h, x : x + w]

                # Recognize face
                name, confidence = self.recognize_face(face_roi)

                if name is not None:
                    recognized_name = name

                    # Store recognition data
                    current_time = datetime.now().strftime("%H:%M:%S")
                    current_date = datetime.now().strftime("%Y-%m-%d")

                    self.current_recognition_data = {
                        "name": name,
                        "time": current_time,
                        "date": current_date,
                        "status": "Present",
                    }

                    # Draw green rectangle around recognized face
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

                    # Add name and confidence labels
                    conf_text = f"{confidence*100:.1f}%"
                    cv2.putText(
                        frame,
                        name,
                        (x, y - 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                    )
                    cv2.putText(
                        frame,
                        conf_text,
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    # Auto record if enabled and cooldown period has passed
                    if self.auto_record_mode and self.can_auto_record(name):
                        if self.save_attendance(
                            current_time, current_date, name, "Present"
                        ):
                            message = f"Auto recorded: {name} - Present"
                            self.speak(message)
                            print(f"🤖 {message}")

                            # Visual feedback for auto recording
                            cv2.putText(
                                frame,
                                "AUTO RECORDED!",
                                (x, y + h + 30),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (0, 255, 0),
                                2,
                            )

                else:
                    # Unknown face detected
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

            # Clear recognition data if no faces detected
            if len(faces) == 0:
                self.current_recognition_data = None

            # Draw touchscreen UI
            frame = self.draw_touchscreen_ui(frame, recognized_name)

            # Show frame
            cv2.imshow("Touchscreen Attendance System", frame)

            # Handle button clicks
            if self.button_clicked:
                self.button_clicked = False  # Reset flag

                if self.current_recognition_data is not None:
                    data = self.current_recognition_data

                    if self.can_process_recognition(data["name"]):
                        # Save attendance
                        if self.save_attendance(
                            data["name"], data["time"], data["date"], data["status"]
                        ):
                            message = f"Attendance recorded: {data['name']} - {data['status']}"
                            self.speak(message)
                            print(f"✅ {message}")

                            # Visual feedback
                            cv2.putText(
                                frame,
                                "RECORDED!",
                                (640, 400),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                2,
                                (0, 255, 0),
                                3,
                            )
                            cv2.imshow("Touchscreen Attendance System", frame)
                            cv2.waitKey(1000)  # Show for 1 second
                        else:
                            print("❌ Failed to save attendance")
                    else:
                        print(
                            f"⏳ Please wait before recording again for {data['name']}"
                        )
                else:
                    print("👤 No face recognized to record attendance")

            # Handle exit button
            if self.exit_clicked:
                break

            # Handle keyboard input as backup (ESC key to exit)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
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
            # Load training data
            if not self.load_training_data():
                return False

            # Initialize camera
            if not self.initialize_camera():
                return False

            # Run attendance system
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


def main():
    """Main function"""
    # System information
    try:
        with open("/proc/cpuinfo", "r") as f:
            if "Raspberry Pi" in f.read():
                print("🍓 Running on Raspberry Pi")
            else:
                print("💻 Running on non-Raspberry Pi system")
    except:
        print("💻 System detection unavailable")

    # Check dependencies
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

    # Run touchscreen attendance system
    system = TouchscreenAttendanceSystem()
    system.run()


if __name__ == "__main__":
    main()
