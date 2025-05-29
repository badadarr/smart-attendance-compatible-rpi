import cv2
import numpy as np
import os
import pickle
from pathlib import Path


def analyze_training_data():
    """Menganalisis data training yang ada dan memperbaikinya jika perlu"""
    print("🔍 Analyzing training data...")

    # Path ke file data
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    names_file = data_dir / "names.pkl"
    faces_file = data_dir / "faces_data.pkl"

    # Cek keberadaan file
    if not faces_file.exists() or not names_file.exists():
        print("❌ Missing training data files")
        return False

    # Load data
    with open(names_file, "rb") as f:
        names = pickle.load(f)

    with open(faces_file, "rb") as f:
        faces = pickle.load(f)

    print(f"\n📊 Current Data Stats:")
    print(f"   - Faces shape: {faces.shape}")
    print(f"   - Features per face: {faces.shape[1]}")
    print(f"   - Total samples: {len(names)}")
    print(f"   - Unique users: {len(set(names))}")
    print(f"   - Users: {set(names)}")

    # Cek konsistensi
    expected_size = 50 * 50  # Ukuran standar 50x50 pixel

    if faces.shape[1] != expected_size:
        print(f"\n⚠️ Inconsistent feature size: {faces.shape[1]}")
        print(f"   Expected: {expected_size} (for 50x50 pixel images)")

        # Mencoba menentukan ukuran asli
        possible_dims = []

        # Cek beberapa kemungkinan ukuran
        sizes = [(50, 50), (75, 100), (86, 87), (50, 150)]
        for h, w in sizes:
            if h * w == faces.shape[1]:
                possible_dims.append((h, w))
            elif abs(h * w - faces.shape[1]) < 10:
                possible_dims.append(f"~{h}x{w}")

        if possible_dims:
            print(f"   Possible dimensions: {possible_dims}")

        # Tanya apakah ingin memperbaiki
        fix = input(
            "\n❓ Would you like to fix the data by converting to 50x50? (y/n): "
        )

        if fix.lower() == "y":
            # Backup data lama
            backup_faces = faces_file.with_suffix(".pkl.bak")
            backup_names = names_file.with_suffix(".pkl.bak")

            with open(backup_faces, "wb") as f:
                pickle.dump(faces, f)
            with open(backup_names, "wb") as f:
                pickle.dump(names, f)

            print(f"✅ Backup created: {backup_faces} and {backup_names}")

            # Ubah ukuran data
            print("\n🔄 Resizing face data...")

            # Cari ukuran terbaik untuk reshape
            best_h, best_w = 0, 0
            for h in range(50, 100):
                if faces.shape[1] % h == 0:
                    w = faces.shape[1] // h
                    if 50 <= w <= 150:
                        best_h, best_w = h, w
                        break

            if best_h == 0:  # Tidak menemukan ukuran yang tepat
                best_h = int(np.sqrt(faces.shape[1]))
                best_w = faces.shape[1] // best_h
                if best_h * best_w != faces.shape[1]:
                    best_w += 1
                    # Pad data jika perlu
                    padding = best_h * best_w - faces.shape[1]
                    if padding > 0:
                        faces = np.hstack((faces, np.zeros((faces.shape[0], padding))))

            print(f"   Reshaping from flat vectors to {best_h}x{best_w} images")

            # Reshape ke gambar
            reshaped_faces = []
            for face_flat in faces:
                try:
                    face_img = face_flat[: best_h * best_w].reshape(best_h, best_w)
                    resized_face = cv2.resize(face_img, (50, 50))
                    reshaped_faces.append(resized_face.flatten())
                except Exception as e:
                    print(f"❌ Error reshaping face: {e}")

            if reshaped_faces:
                fixed_faces = np.array(reshaped_faces)

                # Simpan data baru
                with open(faces_file, "wb") as f:
                    pickle.dump(fixed_faces, f)

                print(f"\n✅ Data successfully resized:")
                print(f"   - New faces shape: {fixed_faces.shape}")
                print(f"   - New features per face: {fixed_faces.shape[1]}")
                return True
            else:
                print("❌ Failed to resize faces")
                return False

        return False
    else:
        print("\n✅ Data is already consistent with 50x50 pixel size")
        return True


if __name__ == "__main__":
    analyze_training_data()
