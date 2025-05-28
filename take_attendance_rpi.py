import cv2
import pickle
import numpy as np
import os
import csv
import time
from datetime import datetime
from sklearn.neighbors import KNeighborsClassifier
from pathlib import Path
import sys

# Try to import speech synthesis (optional)
try:
    import pyttsx3

    SPEECH_AVAILABLE = True
    print("🔊 Text-to-speech available")
except ImportError:
    SPEECH_AVAILABLE = False
    print("🔇 Text-to-speech not available (install pyttsx3 for speech feedback)")


class AttendanceSystem:
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
        try:
            if not self.names_file.exists() or not self.faces_file.exists():
                raise FileNotFoundError("Training data files not found")

            with open(self.names_file, "rb") as f:
                self.labels = pickle.load(f)

            with open(self.faces_file, "rb") as f:
                faces = pickle.load(f)

            print(f"📊 Loaded training data:")
            print(f"   - Faces shape: {faces.shape}")
            print(f"   - Total samples: {len(self.labels)}")
            print(f"   - Unique users: {len(set(self.labels))}")

            # Initialize KNN classifier
            self.knn = KNeighborsClassifier(n_neighbors=5)
            self.knn.fit(faces, self.labels)

            return True

        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            print("💡 Make sure to run add_faces_rpi.py first to register faces")
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
            # Prepare face data
            resized_face = cv2.resize(face_roi, (50, 50))
            face_flattened = resized_face.flatten().reshape(1, -1)

            # Get prediction and probabilities
            prediction = self.knn.predict(face_flattened)[0]
            probabilities = self.knn.predict_proba(face_flattened)[0]
            confidence = max(probabilities)

            # Check confidence threshold
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

    def run_attendance(self):
        """Main attendance recognition loop"""
        print("🎯 Face Recognition Attendance System")
        print("=" * 50)
        print("📝 Instructions:")
        print("   - Press 'SPACE' to record attendance")
        print("   - Press 'q' to quit")
        print("   - Look directly at the camera")
        print("=" * 50)

        frame_count = 0

        while True:
            ret, frame = self.video.read()
            if not ret:
                print("❌ Error reading from camera")
                break

            frame_count += 1

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.3, minNeighbors=5, minSize=(50, 50)
            )

            current_time = datetime.now()
            date_str = current_time.strftime("%d-%m-%Y")
            time_str = current_time.strftime("%H:%M:%S")

            # Process each detected face
            for x, y, w, h in faces:
                face_roi = frame[y : y + h, x : x + w]

                # Recognize face (every 5th frame for performance)
                if frame_count % 5 == 0:
                    name, confidence = self.recognize_face(face_roi)

                    if name:
                        # Get current status
                        current_status = self.get_current_status(name, date_str)
                        next_status = (
                            "CLOCK IN" if current_status != "CLOCK IN" else "CLOCK OUT"
                        )

                        # Draw rectangle and labels
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                        # Status label
                        label = f"{name} - {next_status}"
                        confidence_label = f"Conf: {confidence:.2f}"

                        cv2.putText(
                            frame,
                            label,
                            (x, y - 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2,
                        )
                        cv2.putText(
                            frame,
                            confidence_label,
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            1,
                        )

                        # Store recognition data for space key processing
                        frame.recognition_data = {
                            "name": name,
                            "status": next_status,
                            "time": time_str,
                            "date": date_str,
                            "confidence": confidence,
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
                else:
                    # Just draw rectangle for other frames
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 1)

            # Add instructions
            cv2.putText(
                frame,
                "Press SPACE to record attendance",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "Press 'q' to quit",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

            # Show frame
            cv2.imshow("Attendance System", frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):  # Space key to record attendance
                if hasattr(frame, "recognition_data"):
                    data = frame.recognition_data

                    if self.can_process_recognition(data["name"]):
                        # Save attendance
                        if self.save_attendance(
                            data["name"], data["time"], data["date"], data["status"]
                        ):
                            message = f"Attendance recorded: {data['name']} - {data['status']}"
                            self.speak(message)
                            print(f"✅ {message}")
                        else:
                            print("❌ Failed to save attendance")
                    else:
                        print(
                            f"⏳ Please wait before recording again for {data['name']}"
                        )
                else:
                    print("👤 No face recognized to record attendance")
            elif key == ord("q"):
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

    # Run attendance system
    system = AttendanceSystem()
    system.run()


if __name__ == "__main__":
    main()
