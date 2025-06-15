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
        # Define data directory - point to project root data folder
        self.DATA_DIR = Path(__file__).parent.parent / "data"
        self.DATA_DIR.mkdir(exist_ok=True)

        # Initialize camera with lower resolution for RPi performance
        self.video = None
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # Configuration
        self.SAMPLES_NEEDED = 20
        self.CAPTURE_DURATION = 60  # seconds
        self.IMAGE_SIZE = (50, 50)

    def initialize_camera(self):
        """Initialize camera with optimal settings for Raspberry Pi"""
        try:
            # Try different camera indices (0, 1, 2)
            for camera_idx in [0, 1, 2]:
                self.video = cv2.VideoCapture(camera_idx)
                if self.video.isOpened():
                    print(f"Camera initialized successfully on index {camera_idx}")
                    break
            else:
                raise Exception("No camera found")

            # Set camera properties for better performance on RPi
            self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.video.set(cv2.CAP_PROP_FPS, 15)  # Lower FPS for RPi
            self.video.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Warm up camera
            for _ in range(10):
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

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.3, minNeighbors=5, minSize=(50, 50)
            )

            # Process detected faces
            for x, y, w, h in faces:
                # Extract and resize face
                face_roi = frame[y : y + h, x : x + w]
                resized_face = cv2.resize(face_roi, self.IMAGE_SIZE)

                # Capture every 3rd frame to get variety
                if len(faces_data) < self.SAMPLES_NEEDED and frame_count % 3 == 0:
                    faces_data.append(resized_face)
                    print(f"✅ Captured sample {len(faces_data)}/{self.SAMPLES_NEEDED}")

                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Add label above face
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

            # Add timer and instructions
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
            )  # Show frame
            cv2.imshow("Face Registration", frame)

            frame_count += 1
            key = cv2.waitKey(1) & 0xFF

            # Exit conditions
            if (
                key == ord("q")
                or elapsed_time >= self.CAPTURE_DURATION
                or len(faces_data) >= self.SAMPLES_NEEDED
            ):
                break

        return faces_data

    def check_existing_data(self, name):
        """Check if name already exists in database"""
        names_file = self.DATA_DIR / "names.pkl"

        if names_file.exists():
            try:
                with open(names_file, "rb") as f:
                    existing_names = pickle.load(f)

                # Get unique names from the existing data
                unique_names = list(set(existing_names))

                if name.lower() in [n.lower() for n in unique_names]:
                    return True, unique_names
                else:
                    return False, unique_names
            except:
                return False, []

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
            # Load existing data
            with open(faces_file, "rb") as f:
                existing_faces = pickle.load(f)
            with open(names_file, "rb") as f:
                existing_names = pickle.load(f)

            # Prepare new face data
            new_faces_array = np.array(new_faces)
            new_faces_flattened = new_faces_array.reshape(len(new_faces), -1)

            # Check similarity with existing faces
            for i, existing_face in enumerate(existing_faces):
                for new_face in new_faces_flattened:
                    # Reshape for comparison
                    existing_face_reshaped = existing_face.reshape(1, -1)
                    new_face_reshaped = new_face.reshape(1, -1)

                    # Calculate cosine similarity
                    similarity = cosine_similarity(
                        existing_face_reshaped, new_face_reshaped
                    )[0][0]

                    # If similarity is too high (>0.85), consider it a duplicate
                    if similarity > 0.85:
                        similar_name = existing_names[i]
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

        # Check for existing name
        name_exists, existing_names = self.check_existing_data(name)
        if name_exists:
            print(f"❌ Name '{name}' already exists in database!")
            print(f"📋 Existing names: {', '.join(existing_names)}")

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

        # Check for face similarity
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

        # Prepare data
        faces_data = faces_data[: self.SAMPLES_NEEDED]  # Take only needed samples
        faces_array = np.array(faces_data)
        faces_flattened = faces_array.reshape(self.SAMPLES_NEEDED, -1)

        # File paths
        names_file = self.DATA_DIR / "names.pkl"
        faces_file = self.DATA_DIR / "faces_data.pkl"

        try:
            # If updating existing name, remove old data first
            if name_exists:
                with open(names_file, "rb") as f:
                    existing_names_list = pickle.load(f)
                with open(faces_file, "rb") as f:
                    existing_faces = pickle.load(f)

                # Remove old data for this name
                indices_to_keep = [
                    i
                    for i, n in enumerate(existing_names_list)
                    if n.lower() != name.lower()
                ]

                if indices_to_keep:
                    filtered_names = [existing_names_list[i] for i in indices_to_keep]
                    filtered_faces = existing_faces[indices_to_keep]
                else:
                    filtered_names = []
                    filtered_faces = np.empty((0, faces_flattened.shape[1]))

                # Add new data
                names = filtered_names + [name] * self.SAMPLES_NEEDED
                faces_combined = (
                    np.vstack((filtered_faces, faces_flattened))
                    if len(filtered_faces) > 0
                    else faces_flattened
                )
            else:
                # Load existing names or create new list
                if names_file.exists():
                    with open(names_file, "rb") as f:
                        names = pickle.load(f)
                    names.extend([name] * self.SAMPLES_NEEDED)
                else:
                    names = [name] * self.SAMPLES_NEEDED

                # Load existing faces or create new array
                if faces_file.exists():
                    with open(faces_file, "rb") as f:
                        existing_faces = pickle.load(f)
                    faces_combined = np.vstack((existing_faces, faces_flattened))
                else:
                    faces_combined = faces_flattened

            # Save updated data
            with open(names_file, "wb") as f:
                pickle.dump(names, f)

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
                faces = pickle.load(f)

            # Get unique names and their counts
            unique_names = {}
            for name in names:
                unique_names[name] = unique_names.get(name, 0) + 1

            print(f"\n📋 Existing users in database:")
            print("=" * 40)
            for i, (name, count) in enumerate(unique_names.items(), 1):
                print(f"{i:2d}. {name} ({count} samples)")

            print(f"\n📊 Total users: {len(unique_names)}")
            print(f"📊 Total samples: {len(faces)}")

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

            # Find indices to keep (not matching the name to delete)
            indices_to_keep = [
                i
                for i, name in enumerate(names)
                if name.lower() != name_to_delete.lower()
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
        # Get user name
        name = input("👤 Enter your name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            return

        # Initialize camera
        if not self.initialize_camera():
            print("❌ Failed to initialize camera")
            return

        try:
            # Capture faces
            faces_data = self.capture_faces(name)

            # Save training data
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

    def run_old(self):
        """Original registration process (kept for backward compatibility)"""
        print("🔧 Face Registration System for Raspberry Pi")
        print("=" * 50)

        # Get user name
        name = input("👤 Enter your name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            return

        # Initialize camera
        if not self.initialize_camera():
            print("❌ Failed to initialize camera")
            return

        try:
            # Capture faces
            faces_data = self.capture_faces(name)

            # Save training data
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


def main():
    """Main function"""
    # Check if running on Raspberry Pi
    try:
        with open("/proc/cpuinfo", "r") as f:
            if "Raspberry Pi" in f.read():
                print("🍓 Detected Raspberry Pi system")
            else:
                print("💻 Running on non-Raspberry Pi system")
    except:
        print("💻 System detection unavailable")

    # Run registration
    registration = FaceRegistration()
    registration.run()


if __name__ == "__main__":
    main()
