from flask import Flask, render_template, request, jsonify, Response
import cv2
import pickle
import os
import csv
import time
from datetime import datetime
from pathlib import Path
import threading
import json
import sys

# Handle NumPy import with error handling for Raspberry Pi
try:
    import numpy as np
except ImportError as e:
    print("❌ NumPy import error:", str(e))
    sys.exit(1)

# Handle scikit-learn import
try:
    from sklearn.neighbors import KNeighborsClassifier
except ImportError as e:
    print("❌ Scikit-learn import error:", str(e))
    sys.exit(1)

app = Flask(__name__)


class WebAttendanceSystem:
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

        # CSV columns
        self.csv_columns = ["NAME", "TIME", "DATE", "STATUS"]

        # Recognition settings
        self.confidence_threshold = 0.6
        self.recognition_cooldown = 3  # seconds between recognitions
        self.last_recognition_time = {}
        self.current_recognition_data = None

        # Camera streaming
        self.camera_running = False
        self.camera_thread = None

        # Auto record settings
        self.auto_record_mode = False
        self.last_auto_record = {}
        self.auto_record_cooldown = 5

        # Load training data on startup
        self.load_training_data()
        self.initialize_camera()

    def load_training_data(self):
        """Load trained face data"""
        if not self.names_file.exists() or not self.faces_file.exists():
            print("❌ Training data not found!")
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
            return True

        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            return False

    def initialize_camera(self):
        """Initialize camera"""
        try:
            for camera_idx in [0, 1, 2]:
                self.video = cv2.VideoCapture(camera_idx)
                if self.video.isOpened():
                    print(f"📹 Camera initialized on index {camera_idx}")
                    break
            else:
                raise Exception("No camera found")

            # Set camera properties
            self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.video.set(cv2.CAP_PROP_FPS, 15)
            self.video.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            return True

        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            return False

    def recognize_face(self, face_roi):
        """Recognize face using KNN classifier"""
        try:
            resized_face = cv2.resize(face_roi, (50, 50))
            face_flattened = resized_face.flatten().reshape(1, -1)
            expected_features = 50 * 50 * 3

            if face_flattened.shape[1] != expected_features:
                return None, 0.0

            prediction = self.knn.predict(face_flattened)[0]
            probabilities = self.knn.predict_proba(face_flattened)[0]
            confidence = max(probabilities)

            if confidence >= self.confidence_threshold:
                return prediction, confidence
            else:
                return None, confidence

        except Exception as e:
            return None, 0.0

    def save_attendance(self, name, timestamp, date, status):
        """Save attendance record"""
        attendance_file = self.attendance_dir / f"Attendance_{date}.csv"
        file_exists = attendance_file.exists()

        try:
            with open(attendance_file, "a", newline="") as f:
                writer = csv.writer(f)

                if not file_exists:
                    writer.writerow(self.csv_columns)

                writer.writerow([name, timestamp, date, status])
                return True

        except Exception as e:
            print(f"❌ Error saving attendance: {e}")
            return False

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

    def generate_frames(self):
        """Generate video frames for streaming"""
        while self.camera_running:
            if self.video is None:
                continue

            ret, frame = self.video.read()
            if not ret:
                continue

            # Resize frame
            frame = cv2.resize(frame, (640, 480))

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

            # Process faces
            for x, y, w, h in faces:
                face_roi = frame[y : y + h, x : x + w]
                name, confidence = self.recognize_face(face_roi)

                if name is not None:
                    # Store recognition data
                    current_time = datetime.now().strftime("%H:%M:%S")
                    current_date = datetime.now().strftime("%Y-%m-%d")

                    self.current_recognition_data = {
                        "name": name,
                        "time": current_time,
                        "date": current_date,
                        "status": "Present",
                        "confidence": confidence,
                    }

                    # Draw recognition on frame
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
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
                        f"{confidence*100:.1f}%",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    # Auto record if enabled
                    if self.auto_record_mode and self.can_auto_record(name):
                        if self.save_attendance(
                            name, current_time, current_date, "Present"
                        ):
                            print(f"🤖 Auto recorded: {name}")

                else:
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

            # Encode frame to JPEG
            ret, buffer = cv2.imencode(".jpg", frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )

    def cleanup(self):
        """Clean up resources"""
        self.camera_running = False
        if self.video:
            self.video.release()


# Global instance
attendance_system = WebAttendanceSystem()


@app.route("/")
def index():
    """Main touchscreen interface"""
    return render_template("touchscreen_attendance.html")


@app.route("/video_feed")
def video_feed():
    """Video streaming route"""
    attendance_system.camera_running = True
    return Response(
        attendance_system.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/api/record_attendance", methods=["POST"])
def record_attendance():
    """Record attendance via API"""
    if attendance_system.current_recognition_data is None:
        return jsonify({"success": False, "message": "No face recognized"})

    data = attendance_system.current_recognition_data

    if not attendance_system.can_process_recognition(data["name"]):
        return jsonify(
            {
                "success": False,
                "message": f"Please wait before recording again for {data['name']}",
            }
        )

    if attendance_system.save_attendance(
        data["name"], data["time"], data["date"], data["status"]
    ):
        return jsonify(
            {
                "success": True,
                "message": f"Attendance recorded: {data['name']} - {data['status']}",
                "data": data,
            }
        )
    else:
        return jsonify({"success": False, "message": "Failed to save attendance"})


@app.route("/api/toggle_auto_mode", methods=["POST"])
def toggle_auto_mode():
    """Toggle auto recording mode"""
    attendance_system.auto_record_mode = not attendance_system.auto_record_mode
    status = "ON" if attendance_system.auto_record_mode else "OFF"
    return jsonify(
        {
            "success": True,
            "auto_mode": attendance_system.auto_record_mode,
            "message": f"Auto mode: {status}",
        }
    )


@app.route("/api/status")
def get_status():
    """Get current system status"""
    return jsonify(
        {
            "auto_mode": attendance_system.auto_record_mode,
            "current_recognition": attendance_system.current_recognition_data,
            "has_training_data": attendance_system.knn is not None,
        }
    )


@app.route("/api/attendance_today")
def attendance_today():
    """Get today's attendance records"""
    today = datetime.now().strftime("%Y-%m-%d")
    attendance_file = attendance_system.attendance_dir / f"Attendance_{today}.csv"

    if not attendance_file.exists():
        return jsonify({"records": []})

    try:
        records = []
        with open(attendance_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return jsonify({"records": records})
    except Exception as e:
        return jsonify({"records": [], "error": str(e)})


if __name__ == "__main__":
    print("🌐 Starting Touchscreen Web Attendance System")
    print("📱 Access via: http://raspberry-pi-ip:5001")
    print("🔧 Use this interface for touchscreen displays")

    try:
        app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n⚠️ Shutting down...")
    finally:
        attendance_system.cleanup()
