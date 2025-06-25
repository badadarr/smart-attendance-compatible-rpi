import cv2
import pickle
import os
import time
import sys
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
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError as e:
    print("⚠️  Scikit-learn not available - face similarity checking disabled")
    print("💡 Install with: pip install scikit-learn")
    SKLEARN_AVAILABLE = False


class FaceRegistration:
    def __init__(self):
        self.DATA_DIR = Path(__file__).parent.parent / "data"
        self.DATA_DIR.mkdir(exist_ok=True)

        self.video = None
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        self.SAMPLES_NEEDED = 20
        self.CAPTURE_DURATION = 60  # seconds
        self.IMAGE_SIZE = (50, 50)  # Target image size for training
        self.EXPECTED_FEATURES = (
            self.IMAGE_SIZE[0] * self.IMAGE_SIZE[1] * 3
        )  # Assuming color images (50x50x3)

    def initialize_camera(self):
        """Initialize camera with optimal settings for Raspberry Pi"""
        try:
            for camera_idx in [0, 1, 2]:
                self.video = cv2.VideoCapture(camera_idx)
                if self.video.isOpened():
                    print(f"Camera initialized successfully on index {camera_idx}")
                    break
            else:
                raise Exception("No camera found")

            self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.video.set(cv2.CAP_PROP_FPS, 15)
            self.video.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            for _ in range(10):  # Warm up camera
                ret, frame = self.video.read()
                if not ret:
                    raise Exception("Camera not responding")

            return True

        except Exception as e:
            print(f"Error initializing camera: {e}")
            return False

    def capture_faces(self, name):
        """Capture face samples for training"""
        faces_data = []
        frame_count = 0
        start_time = time.time()

        print(f"\n🎥 Starting face capture for: {name}")
        print(f"📝 Instructions:")
        print(f"   - Look directly at the camera")
        print(f"   - Move your head slightly (left, right, up, down)")
        print(f"   - Keep good lighting on your face")
        print(f"   - Capture will run for {self.CAPTURE_DURATION} seconds")
        print(f"   - Press 'q' to quit early")
        print(f"   - Recording starts in 3 seconds...\n")

        time.sleep(3)

        while True:
            ret, frame = self.video.read()
            if not ret:
                print("❌ Error reading from camera")
                break

            current_time = time.time()
            elapsed_time = current_time - start_time
            remaining_time = max(self.CAPTURE_DURATION - int(elapsed_time), 0)

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.3, minNeighbors=5, minSize=(50, 50)
            )

            for x, y, w, h in faces:
                face_roi = frame[y : y + h, x : x + w]
                resized_face = cv2.resize(face_roi, self.IMAGE_SIZE)

                if len(faces_data) < self.SAMPLES_NEEDED and frame_count % 3 == 0:
                    faces_data.append(resized_face)
                    print(f"✅ Captured sample {len(faces_data)}/{self.SAMPLES_NEEDED}")

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                label = f"{name} - Sample {len(faces_data)}/{self.SAMPLES_NEEDED}"
                cv2.putText(
                    frame,
                    label,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

            cv2.putText(
                frame,
                f"Time: {remaining_time}s",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                f"Samples: {len(faces_data)}/{self.SAMPLES_NEEDED}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                frame,
                "Press 'q' to quit",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )
            cv2.imshow("Face Registration", frame)

            frame_count += 1
            key = cv2.waitKey(1) & 0xFF

            if (
                key == ord("q")
                or elapsed_time >= self.CAPTURE_DURATION
                or len(faces_data) >= self.SAMPLES_NEEDED
            ):
                break

        return faces_data

    def check_existing_data(self, name):
        """Check if name already exists in database and return unique names"""
        names_file = self.DATA_DIR / "names.pkl"

        if not names_file.exists():
            return False, []

        try:
            with open(names_file, "rb") as f:
                existing_names = pickle.load(f)
            unique_names = list(set(existing_names))

            return name.lower() in [n.lower() for n in unique_names], unique_names
        except Exception as e:
            print(f"Error checking existing data: {e}")
            return False, []

    def check_face_similarity(self, new_faces):
        """Check if captured face is similar to existing faces"""
        if not SKLEARN_AVAILABLE:
            print("⚠️  Face similarity checking disabled (scikit-learn not available)")
            return False, None

        faces_file = self.DATA_DIR / "faces_data.pkl"
        names_file = self.DATA_DIR / "names.pkl"

        if not faces_file.exists() or not names_file.exists():
            return False, None

        try:
            with open(faces_file, "rb") as f:
                existing_faces_raw = pickle.load(f)
            with open(names_file, "rb") as f:
                existing_names = pickle.load(f)

            # Ensure existing_faces_raw is a numpy array
            if not isinstance(existing_faces_raw, np.ndarray):
                existing_faces_raw = np.array(existing_faces_raw)

            # Reshape existing faces to 2D array if they are 3D (color images)
            if existing_faces_raw.ndim == 4:  # e.g., (N, 50, 50, 3)
                existing_faces_flattened = existing_faces_raw.reshape(
                    existing_faces_raw.shape[0], -1
                )
            elif existing_faces_raw.ndim == 2:  # e.g., (N, 7500)
                existing_faces_flattened = existing_faces_raw
            else:
                print(
                    f"⚠️ Unexpected existing_faces_raw dimensions: {existing_faces_raw.shape}"
                )
                return False, None

            new_faces_array = np.array(new_faces)
            new_faces_flattened = new_faces_array.reshape(len(new_faces), -1)

            # Ensure feature count matches for comparison (e.g., both 7500 for color, or 2500 for grayscale)
            # This is a critical point for compatibility.
            if existing_faces_flattened.shape[1] != new_faces_flattened.shape[1]:
                print(
                    f"⚠️ Feature count mismatch between existing and new faces: {existing_faces_flattened.shape[1]} vs {new_faces_flattened.shape[1]}"
                )
                # A more robust solution might involve converting one to match the other,
                # but for now, we'll assume consistency or return False.
                return False, None

            # Check similarity with existing faces
            # Use a slightly optimized loop, or consider a single similarity matrix calculation
            for i, existing_face_flat in enumerate(existing_faces_flattened):
                # Calculate cosine similarity with all new faces
                similarities = cosine_similarity(
                    existing_face_flat.reshape(1, -1), new_faces_flattened
                )

                # If any new face is highly similar to this existing face
                if np.any(similarities > 0.85):
                    similar_name = existing_names[
                        i
                    ]  # This might not be the exact name if existing_names is flat and faces is flat
                    # A more accurate way to get the name would be to map back to unique names
                    # For simplicity, we assume existing_names maps 1-to-1 with existing_faces_flattened here.
                    return True, similar_name

            return False, None

        except Exception as e:
            print(f"⚠️  Error checking face similarity: {e}")
            return False, None

    def save_training_data(self, name, faces_data):
        """Save captured faces to training files with duplicate checking"""
        if len(faces_data) < self.SAMPLES_NEEDED:
            print(f"❌ Insufficient samples: {len(faces_data)}/{self.SAMPLES_NEEDED}")
            print("💡 Try again with better lighting conditions")
            return False

        name_exists, existing_unique_names = self.check_existing_data(name)
        if name_exists:
            print(f"❌ Name '{name}' already exists in database!")
            print(f"📋 Existing names: {', '.join(existing_unique_names)}")
            response = (
                input(f"Do you want to update existing data for '{name}'? (y/n): ")
                .strip()
                .lower()
            )
            if response != "y":
                print("❌ Registration cancelled")
                return False
            else:
                print(f"⚠️  Updating existing data for '{name}'...")

        print("🔍 Checking for similar faces in database...")
        face_exists, similar_name = self.check_face_similarity(faces_data)
        if face_exists:
            print(f"❌ Similar face detected! This face looks like '{similar_name}'")
            print(f"💡 Each person should register only once")
            response = (
                input(
                    f"Are you sure this is a different person from '{similar_name}'? (y/n): "
                )
                .strip()
                .lower()
            )
            if response != "y":
                print("❌ Registration cancelled to prevent duplicates")
                return False

        faces_data_to_save = faces_data[: self.SAMPLES_NEEDED]
        faces_array = np.array(faces_data_to_save)
        faces_flattened = faces_array.reshape(self.SAMPLES_NEEDED, -1)

        names_file = self.DATA_DIR / "names.pkl"
        faces_file = self.DATA_DIR / "faces_data.pkl"

        try:
            # Load existing data (if any) or initialize empty lists/arrays
            existing_names_list = []
            existing_faces_array = np.empty((0, self.EXPECTED_FEATURES))

            if names_file.exists():
                with open(names_file, "rb") as f:
                    existing_names_list = pickle.load(f)
            if faces_file.exists():
                with open(faces_file, "rb") as f:
                    existing_faces_raw = pickle.load(f)
                    if not isinstance(
                        existing_faces_raw, np.ndarray
                    ):  # Convert if not already numpy array
                        existing_faces_raw = np.array(existing_faces_raw)
                    if existing_faces_raw.ndim == 4:  # e.g. (N, 50, 50, 3)
                        existing_faces_array = existing_faces_raw.reshape(
                            existing_faces_raw.shape[0], -1
                        )
                    elif (
                        existing_faces_raw.ndim == 2
                        and existing_faces_raw.shape[1] == self.EXPECTED_FEATURES
                    ):
                        existing_faces_array = existing_faces_raw
                    else:
                        print(
                            f"⚠️ Warning: Existing faces data has unexpected shape or feature count: {existing_faces_raw.shape}. Skipping old data."
                        )
                        existing_faces_array = np.empty(
                            (0, self.EXPECTED_FEATURES)
                        )  # Reset if incompatible

            # If updating, remove old data for this name
            if name_exists:
                indices_to_keep = [
                    i
                    for i, n in enumerate(existing_names_list)
                    if n.lower() != name.lower()
                ]
                filtered_names = [existing_names_list[i] for i in indices_to_keep]
                filtered_faces = existing_faces_array[indices_to_keep]
            else:
                filtered_names = existing_names_list
                filtered_faces = existing_faces_array

            # Add new data
            names_combined = filtered_names + [name] * self.SAMPLES_NEEDED
            faces_combined = np.vstack((filtered_faces, faces_flattened))

            # Save updated data
            with open(names_file, "wb") as f:
                pickle.dump(names_combined, f)
            with open(faces_file, "wb") as f:
                pickle.dump(faces_combined, f)

            print(f"✅ Successfully registered {name}")
            print(f"📁 Data saved to: {self.DATA_DIR}")
            print(f"📊 Total samples in database: {len(faces_combined)}")

            return True

        except Exception as e:
            print(f"❌ Error saving data: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        if self.video:
            self.video.release()
        cv2.destroyAllWindows()

    def show_existing_users(self):
        """Display existing users in database"""
        names_file = self.DATA_DIR / "names.pkl"
        faces_file = self.DATA_DIR / "faces_data.pkl"

        if not names_file.exists() or not faces_file.exists():
            print("📝 No existing users found in database")
            return []

        try:
            with open(names_file, "rb") as f:
                names = pickle.load(f)
            with open(faces_file, "rb") as f:
                faces = pickle.load(
                    f
                )  # Just to get total count, not used for individual users

            unique_names = {}
            for name in names:
                unique_names[name] = unique_names.get(name, 0) + 1

            print(f"\n📋 Existing users in database:")
            print("=" * 40)
            if unique_names:
                for i, (name_key, count) in enumerate(unique_names.items(), 1):
                    print(f"{i:2d}. {name_key} ({count} samples)")
            else:
                print("   (No unique users found)")

            print(f"\n📊 Total users: {len(unique_names)}")
            print(
                f"📊 Total samples in data file: {len(names) if names else 0}"
            )  # Use len(names) for actual saved samples

            return list(unique_names.keys())

        except Exception as e:
            print(f"❌ Error reading database: {e}")
            return []

    def delete_user(self, name_to_delete):
        """Delete a user from the database"""
        names_file = self.DATA_DIR / "names.pkl"
        faces_file = self.DATA_DIR / "faces_data.pkl"

        if not names_file.exists() or not faces_file.exists():
            print("❌ No database found")
            return False

        try:
            with open(names_file, "rb") as f:
                names = pickle.load(f)
            with open(faces_file, "rb") as f:
                faces = pickle.load(f)

            if not isinstance(faces, np.ndarray):
                faces = np.array(faces)

            # Find indices to keep (not matching the name to delete)
            # Ensure case-insensitive comparison
            indices_to_keep = [
                i
                for i, name_item in enumerate(names)
                if name_item.lower() != name_to_delete.lower()
            ]

            if len(indices_to_keep) == len(names):
                print(f"❌ User '{name_to_delete}' not found in database")
                return False

            # Filter data
            filtered_names = [names[i] for i in indices_to_keep]
            filtered_faces = faces[indices_to_keep]

            # Save filtered data
            with open(names_file, "wb") as f:
                pickle.dump(filtered_names, f)
            with open(faces_file, "wb") as f:
                pickle.dump(filtered_faces, f)

            samples_removed = len(names) - len(filtered_names)
            print(f"✅ User '{name_to_delete}' deleted successfully")
            print(f"📊 Removed {samples_removed} samples")

            return True

        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False

    def run(self):
        """Main registration process with enhanced menu"""
        print("🔧 Face Registration System for Raspberry Pi")
        print("=" * 50)

        while True:
            print(f"\n📋 Options:")
            print(f"1. Register new face")
            print(f"2. View existing users")
            print(f"3. Delete user")
            print(f"4. Exit")

            choice = input(f"\nSelect option (1-4): ").strip()

            if choice == "1":
                self.register_new_face()
            elif choice == "2":
                self.show_existing_users()
            elif choice == "3":
                self.delete_user_menu()
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option. Please select 1-4.")

    def register_new_face(self):
        """Register a new face"""
        name = input("👤 Enter your name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            return

        if not self.initialize_camera():
            print("❌ Failed to initialize camera")
            return

        try:
            faces_data = self.capture_faces(name)

            if faces_data:
                success = self.save_training_data(name, faces_data)
                if success:
                    print(f"\n🎉 Registration completed successfully!")
                    print(f"👤 User: {name}")
                    print(f"📸 Samples captured: {len(faces_data)}")
                    print(f"\n💡 You can now use the attendance system!")
                else:
                    print(f"\n❌ Registration failed")
            else:
                print(f"\n❌ No face samples captured")

        except KeyboardInterrupt:
            print(f"\n⚠️  Registration cancelled by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            self.cleanup()

    def delete_user_menu(self):
        """Delete user menu"""
        existing_users = self.show_existing_users()

        if not existing_users:
            return

        print(f"\n🗑️  Delete User")
        name_to_delete = input("Enter name to delete (or 'cancel' to abort): ").strip()

        if name_to_delete.lower() == "cancel":
            print("❌ Delete cancelled")
            return

        if name_to_delete.lower() in [name.lower() for name in existing_users]:
            confirm = (
                input(f"⚠️  Are you sure you want to delete '{name_to_delete}'? (y/n): ")
                .strip()
                .lower()
            )
            if confirm == "y":
                self.delete_user(name_to_delete)
            else:
                print("❌ Delete cancelled")
        else:
            print(f"❌ User '{name_to_delete}' not found")


def main():
    """Main function"""
    try:
        with open("/proc/cpuinfo", "r") as f:
            if "Raspberry Pi" in f.read():
                print("🍓 Detected Raspberry Pi system")
            else:
                print("💻 Running on non-Raspberry Pi system")
    except:
        print("💻 System detection unavailable")

    registration = FaceRegistration()
    registration.run()


if __name__ == "__main__":
    main()
