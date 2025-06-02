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


class AttendanceSystem:
    def __init__(self):
        # Paths
        self.base_dir = Path(__file__).parent.parent  # Go up to project root
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
                print(
                    "⚠️  Could not initialize text-to-speech"
                )  # CSV columns - Updated for clock in/clock out system
        self.csv_columns = [
            "NAME",
            "TIME",
            "DATE",
            "STATUS",
            "WORK_HOURS",
        ]  # Recognition settings
        self.confidence_threshold = 0.6
        self.recognition_cooldown = 3  # seconds between recognitions
        self.last_recognition_time = {}
        self.current_recognition_data = None  # Store current recognition data

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
        """Save attendance record with work hours calculation"""
        attendance_file = self.attendance_dir / f"Attendance_{date}.csv"
        file_exists = attendance_file.exists()

        try:
            # Calculate work hours if this is a Clock Out
            work_hours = ""
            if status == "Clock Out":
                work_hours = self.calculate_work_hours(name, date, timestamp)

            with open(attendance_file, "a", newline="") as f:
                writer = csv.writer(f)

                # Write header if new file
                if not file_exists:
                    writer.writerow(self.csv_columns)

                # Write attendance record
                writer.writerow([name, timestamp, date, status, work_hours])
                return True

        except Exception as e:
            print(f"❌ Error saving attendance: {e}")
            return False

    def calculate_work_hours(self, name, date, clock_out_time):
        """Calculate work hours between clock in and clock out"""
        attendance_file = self.attendance_dir / f"Attendance_{date}.csv"

        if not attendance_file.exists():
            return ""

        try:
            with open(attendance_file, "r") as f:
                reader = csv.DictReader(f)
                records = [row for row in reader if row["NAME"] == name]

                # Find the last Clock In time
                clock_in_time = None
                for record in reversed(records):
                    if record["STATUS"] == "Clock In":
                        clock_in_time = record["TIME"]
                        break

                if clock_in_time:
                    # Calculate hours difference
                    from datetime import datetime

                    time_format = "%H:%M:%S"

                    clock_in_dt = datetime.strptime(clock_in_time, time_format)
                    clock_out_dt = datetime.strptime(clock_out_time, time_format)

                    # Handle case where clock out is next day
                    if clock_out_dt < clock_in_dt:
                        from datetime import timedelta

                        clock_out_dt += timedelta(days=1)

                    time_diff = clock_out_dt - clock_in_dt
                    hours = time_diff.total_seconds() / 3600
                    return f"{hours:.1f}"

                return ""

        except Exception as e:
            print(f"❌ Error calculating work hours: {e}")
            return ""

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

        # Load background image
        groupbg_path = str(self.base_dir / "groupbg.png")
        groupbg = cv2.imread(groupbg_path)
        if groupbg is None:
            print(f"❌ Failed to load background image: {groupbg_path}")
            return

        while True:
            ret, frame = self.video.read()
            if not ret:
                print("❌ Error reading from camera")
                break

            frame_count += 1

            # Deteksi wajah dengan parameter yang lebih sensitif
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Equalize histogram untuk memperbaiki kontras
            gray = cv2.equalizeHist(gray)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,  # Nilai lebih besar = lebih sensitif
                minNeighbors=3,  # Nilai lebih kecil = lebih sensitif
                minSize=(20, 20),  # Ukuran minimum wajah yang lebih kecil
                maxSize=(300, 300),  # Ukuran maximum wajah
            )  # Process setiap wajah yang terdeteksi
            for x, y, w, h in faces:
                # Crop area wajah from original color frame (not grayscale)
                face_roi = frame[y : y + h, x : x + w]  # Recognize face
                name, confidence = self.recognize_face(face_roi)

                if name is not None:
                    # Store recognition data for use when space key is pressed
                    current_time = datetime.now().strftime("%H:%M:%S")
                    current_date = datetime.now().strftime("%Y-%m-%d")

                    # Determine Clock In or Clock Out based on current status
                    current_status = self.get_current_status(name, current_date)
                    if current_status is None or current_status == "Clock Out":
                        status = "Clock In"
                    else:
                        status = "Clock Out"

                    self.current_recognition_data = {
                        "name": name,
                        "time": current_time,
                        "date": current_date,
                        "status": status,
                    }

                    # Gambar rectangle di sekitar wajah
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Tambahkan text nama dan confidence
                    conf_text = f"{confidence*100:.2f}%"
                    cv2.putText(
                        frame,
                        name,
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )
                    cv2.putText(
                        frame,
                        conf_text,
                        (x, y + h + 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )
                else:
                    # Wajah terdeteksi tapi tidak dikenali
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(
                        frame,
                        "Unknown",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        2,
                    )

            # Clear recognition data if no faces are detected
            if len(faces) == 0:
                self.current_recognition_data = None

            # Resize background dan frame
            frame_height, frame_width = frame.shape[:2]
            desired_width = 1280  # Lebar tampilan yang diinginkan
            desired_height = 720  # Tinggi tampilan yang diinginkan

            # Mengubah ukuran frame video agar sesuai dengan area biru
            frame_desired_width = 640  # Sesuaikan dengan lebar area biru
            frame_desired_height = 480  # Sesuaikan dengan tinggi area biru
            frame = cv2.resize(frame, (frame_desired_width, frame_desired_height))
            frame_height, frame_width = frame.shape[:2]

            # Resize background
            background = cv2.resize(groupbg, (desired_width, desired_height))

            # Hitung posisi frame video di area biru (sesuaikan dengan posisi area biru di groupbg)
            frame_x = 80  # Jarak dari kiri
            frame_y = 150  # Jarak dari atas, di bawah tulisan Face Attendance System

            # Embed video frame di area biru
            try:
                background[
                    frame_y : frame_y + frame_height, frame_x : frame_x + frame_width
                ] = frame
            except:
                print("❌ Error embedding frame into background")
                continue

            # Add title (di atas frame video)
            title_text = "Face Attendance System"
            title_font = cv2.FONT_HERSHEY_SIMPLEX
            title_scale = 1.5
            title_thickness = 2
            title_color = (255, 255, 255)

            # Ukur ukuran text untuk penempatan yang tepat
            (title_width, title_height), _ = cv2.getTextSize(
                title_text, title_font, title_scale, title_thickness
            )
            title_x = (desired_width - title_width) // 2
            title_y = 80  # Sesuaikan dengan posisi judul yang diinginkan

            cv2.putText(
                background,
                title_text,
                (title_x, title_y),
                title_font,
                title_scale,
                title_color,
                title_thickness,
            )

            # Add instructions (di bawah frame video)
            instructions = ["Press 'SPACE' to record attendance", "Press 'q' to quit"]

            inst_y = frame_y + frame_height + 30
            for instruction in instructions:
                (inst_width, inst_height), _ = cv2.getTextSize(
                    instruction, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2
                )
                inst_x = (
                    frame_x + (frame_width - inst_width) // 2
                )  # Tengah dari area frame

                # Tambah shadow untuk keterbacaan
                cv2.putText(
                    background,
                    instruction,
                    (inst_x + 2, inst_y + 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 0),
                    2,
                )
                cv2.putText(
                    background,
                    instruction,
                    (inst_x, inst_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                )
                inst_y += 40

            # Show frame
            cv2.imshow("Attendance System", background)  # Handle key presses
            key = cv2.waitKey(1) & 0xFF

            if key == ord(" "):  # Space key to record attendance
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
