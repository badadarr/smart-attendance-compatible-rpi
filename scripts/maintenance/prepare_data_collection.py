#!/usr/bin/env python3
"""
Pre-Collection Setup Script
Validates system readiness before collecting new face data
"""

import cv2
import os
from pathlib import Path
import sys


def check_camera():
    """Test camera functionality"""
    print("📹 Testing camera...")

    try:
        # Try different camera indices
        camera_found = False
        for camera_idx in [0, 1, 2]:
            cap = cv2.VideoCapture(camera_idx)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"✅ Camera found on index {camera_idx}")
                    print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
                    camera_found = True

                    # Test face detection
                    face_cascade = cv2.CascadeClassifier(
                        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                    )
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                    if len(faces) > 0:
                        print(
                            f"   Face detection: ✅ Working ({len(faces)} face(s) detected)"
                        )
                    else:
                        print(
                            "   Face detection: ⚠️  No faces detected (normal if no one in front of camera)"
                        )

                    cap.release()
                    break
                cap.release()

        if not camera_found:
            print("❌ No working camera found")
            return False

        return True

    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False


def check_directories():
    """Ensure required directories exist"""
    print("\n📁 Checking directories...")

    base_dir = Path(__file__).parent
    required_dirs = ["data", "Attendance"]

    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"✅ Created directory: {dir_name}")
        else:
            print(f"✅ Directory exists: {dir_name}")

    return True


def check_existing_data():
    """Check what data currently exists"""
    print("\n📊 Checking existing data...")

    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"
    attendance_dir = base_dir / "Attendance"

    # Check face data
    face_files = ["faces_data.pkl", "names.pkl"]
    face_data_exists = []

    for filename in face_files:
        file_path = data_dir / filename
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"📄 {filename}: {size} bytes")
            face_data_exists.append(filename)
        else:
            print(f"📄 {filename}: Not found")

    # Check attendance files
    if attendance_dir.exists():
        csv_files = list(attendance_dir.glob("*.csv"))
        if csv_files:
            print(f"📄 Attendance files: {len(csv_files)} found")
            for csv_file in csv_files:
                size = csv_file.stat().st_size
                print(f"   {csv_file.name}: {size} bytes")
        else:
            print("📄 Attendance files: None found")
    else:
        print("📄 Attendance files: Directory not found")

    return len(face_data_exists) > 0


def check_dependencies():
    """Check if required Python packages are available"""
    print("\n🐍 Checking Python dependencies...")

    required_packages = [
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("sklearn", "Scikit-learn"),
        ("pickle", "Pickle (built-in)"),
        ("csv", "CSV (built-in)"),
    ]

    missing_packages = []

    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name}: Available")
        except ImportError:
            print(f"❌ {name}: Missing")
            missing_packages.append(name)

    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install opencv-python numpy scikit-learn")
        return False

    return True


def print_collection_tips():
    """Print tips for successful data collection"""
    print("\n" + "=" * 60)
    print("💡 TIPS PENGUMPULAN DATA YANG BERHASIL")
    print("=" * 60)

    print("\n🎯 Persiapan:")
    print("• Pastikan ruangan memiliki pencahayaan yang cukup")
    print("• Posisi kamera setinggi mata")
    print("• Jarak optimal: 50-100 cm dari kamera")
    print("• Background yang tidak terlalu ramai")

    print("\n📸 Saat mengambil foto:")
    print("• Wajah menghadap langsung ke kamera")
    print("• Jangan pakai topi, kacamata hitam, atau masker")
    print("• Ekspresi netral dan tersenyum")
    print("• Ambil dari berbagai sudut sedikit:")
    print("  - Depan langsung")
    print("  - Sedikit ke kiri")
    print("  - Sedikit ke kanan")
    print("  - Sedikit menunduk")
    print("  - Sedikit mendongak")

    print("\n👥 Untuk setiap orang:")
    print("• Minimal 30-50 foto untuk akurasi tinggi")
    print("• Pastikan nama dieja dengan benar")
    print("• Gunakan nama yang sama untuk satu orang")
    print("• Jangan ada spasi di awal/akhir nama")

    print("\n⚠️  Yang harus dihindari:")
    print("• Pencahayaan terlalu gelap atau terlalu terang")
    print("• Wajah terlalu dekat atau terlalu jauh")
    print("• Bergerak terlalu cepat saat pengambilan foto")
    print("• Menggunakan nama yang berbeda untuk orang yang sama")

    print("\n🔄 Setelah pengumpulan:")
    print("• Test recognition dengan memanggil semua nama")
    print("• Jika ada yang tidak akurat, kumpulkan lebih banyak foto")
    print("• Simpan backup data faces_data.pkl dan names.pkl")


def print_next_steps():
    """Print what to do next"""
    print("\n" + "=" * 60)
    print("🚀 LANGKAH SELANJUTNYA")
    print("=" * 60)

    print("\n1. 🧹 Reset data lama (jika diperlukan):")
    print("   python reset_data.py")

    print("\n2. 📸 Kumpulkan data wajah baru:")
    print("   python add_faces_rpi.py")

    print("\n3. 🧪 Test sistem:")
    print("   python take_attendance_touchscreen.py")

    print("\n4. 📊 Lihat laporan:")
    print("   python attendance_reports.py")

    print("\n5. 🔄 Jika ada masalah, ulangi dari langkah 2")


def main():
    """Main validation function"""
    print("🔍 Pre-Collection System Check")
    print("=" * 40)
    print("Checking system readiness for face data collection...")

    checks_passed = 0
    total_checks = 4

    # Run all checks
    if check_dependencies():
        checks_passed += 1

    if check_directories():
        checks_passed += 1

    if check_camera():
        checks_passed += 1

    has_existing_data = check_existing_data()
    checks_passed += 1  # This check always "passes"

    # Summary
    print("\n" + "=" * 50)
    print("📊 SYSTEM READINESS SUMMARY")
    print("=" * 50)

    print(f"✅ Checks passed: {checks_passed}/{total_checks}")

    if checks_passed == total_checks:
        print("🎉 System is ready for data collection!")

        if has_existing_data:
            print("\n⚠️  PERHATIAN: Data lama ditemukan!")
            print("Anda mungkin ingin menghapus data lama terlebih dahulu.")
            print("Jalankan: python reset_data.py")

        print_collection_tips()
        print_next_steps()

    else:
        print("❌ System not ready. Please fix the issues above.")
        return False

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
