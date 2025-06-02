#!/usr/bin/env python3
"""
Pre-Collection Validator
Script untuk memvalidasi kesiapan sistem sebelum mengumpulkan data wajah baru
"""

import os
import cv2
import numpy as np
from pathlib import Path
import csv
from datetime import datetime
import subprocess
import sys


class PreCollectionValidator:
    def __init__(self):
        """Initialize pre-collection validator"""
        self.base_dir = Path(".")
        self.faces_dir = self.base_dir / "faces"
        self.attendance_dir = self.base_dir / "Attendance"
        self.trainer_dir = self.base_dir / "trainer"

        self.validation_results = []

    def check_opencv_installation(self):
        """Check OpenCV installation and camera access"""
        print("📷 Checking OpenCV and Camera...")

        try:
            # Check OpenCV version
            cv_version = cv2.__version__
            self.validation_results.append(f"✅ OpenCV Version: {cv_version}")

            # Try to access camera
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    height, width = frame.shape[:2]
                    self.validation_results.append(
                        f"✅ Camera Access: Working ({width}x{height})"
                    )
                    cap.release()
                    return True
                else:
                    self.validation_results.append(
                        "❌ Camera Access: Can't read frames"
                    )
                    cap.release()
                    return False
            else:
                self.validation_results.append("❌ Camera Access: Can't open camera")
                return False

        except Exception as e:
            self.validation_results.append(f"❌ OpenCV Error: {str(e)}")
            return False

    def check_directory_structure(self):
        """Check if directory structure is ready"""
        print("📁 Checking Directory Structure...")

        required_dirs = [
            ("faces", self.faces_dir),
            ("Attendance", self.attendance_dir),
            ("trainer", self.trainer_dir),
        ]

        all_good = True

        for name, path in required_dirs:
            if path.exists():
                if name == "faces" and list(path.glob("*")):
                    # faces directory should be empty for fresh collection
                    file_count = len(list(path.glob("*")))
                    self.validation_results.append(
                        f"⚠️ {name}/: Contains {file_count} items (should be empty)"
                    )
                    all_good = False
                else:
                    self.validation_results.append(f"✅ {name}/: Ready")
            else:
                # Create missing directories
                path.mkdir(exist_ok=True)
                self.validation_results.append(f"✅ {name}/: Created")

        return all_good

    def check_required_scripts(self):
        """Check if all required scripts are present"""
        print("📜 Checking Required Scripts...")

        required_scripts = [
            ("take_pics.py", "Data collection script"),
            ("train_faces.py", "Model training script"),
            ("take_attendance_touchscreen.py", "Main attendance system"),
            ("attendance_reports.py", "Reporting system"),
        ]

        all_present = True

        for script, description in required_scripts:
            script_path = self.base_dir / script
            if script_path.exists():
                # Check if script is executable
                if os.access(script_path, os.R_OK):
                    self.validation_results.append(f"✅ {script}: Present & Readable")
                else:
                    self.validation_results.append(
                        f"⚠️ {script}: Present but not readable"
                    )
                    all_present = False
            else:
                self.validation_results.append(f"❌ {script}: Missing")
                all_present = False

        return all_present

    def check_python_dependencies(self):
        """Check if required Python packages are installed"""
        print("🐍 Checking Python Dependencies...")

        required_packages = [
            ("cv2", "OpenCV"),
            ("numpy", "NumPy"),
            ("sklearn", "Scikit-learn"),
            ("PIL", "Pillow (optional)"),
        ]

        all_installed = True

        for module, name in required_packages:
            try:
                if module == "sklearn":
                    import sklearn
                elif module == "PIL":
                    from PIL import Image
                else:
                    __import__(module)
                self.validation_results.append(f"✅ {name}: Installed")
            except ImportError:
                if module == "PIL":
                    self.validation_results.append(
                        f"⚠️ {name}: Not installed (optional)"
                    )
                else:
                    self.validation_results.append(f"❌ {name}: Not installed")
                    all_installed = False

        return all_installed

    def check_attendance_file_format(self):
        """Check if attendance file has correct format"""
        print("📊 Checking Attendance File Format...")

        today = datetime.now().strftime("%Y-%m-%d")
        attendance_file = self.attendance_dir / f"Attendance_{today}.csv"

        expected_headers = ["NAME", "TIME", "DATE", "STATUS", "WORK_HOURS"]

        if attendance_file.exists():
            try:
                with open(attendance_file, "r", encoding="utf-8") as file:
                    reader = csv.reader(file)
                    headers = next(reader, None)

                    if headers == expected_headers:
                        self.validation_results.append(
                            f"✅ Attendance File: Correct format"
                        )
                        return True
                    else:
                        self.validation_results.append(
                            f"❌ Attendance File: Wrong headers - {headers}"
                        )
                        return False

            except Exception as e:
                self.validation_results.append(
                    f"❌ Attendance File: Error reading - {str(e)}"
                )
                return False
        else:
            # Create attendance file with correct headers
            try:
                with open(attendance_file, "w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(expected_headers)
                self.validation_results.append(
                    f"✅ Attendance File: Created with correct format"
                )
                return True
            except Exception as e:
                self.validation_results.append(
                    f"❌ Attendance File: Failed to create - {str(e)}"
                )
                return False

    def check_storage_space(self):
        """Check available storage space"""
        print("💾 Checking Storage Space...")

        try:
            # Get available space
            statvfs = os.statvfs(".")
            available_bytes = statvfs.f_frsize * statvfs.f_bavail
            available_mb = available_bytes / (1024 * 1024)

            # Estimate space needed:
            # - 50 photos per person × 5 people × 200KB per photo = ~50MB
            # - Training data and models = ~10MB
            # - Attendance logs = ~1MB
            # Total estimated: ~61MB, recommend minimum 100MB

            if available_mb > 100:
                self.validation_results.append(
                    f"✅ Storage Space: {available_mb:.1f}MB available"
                )
                return True
            elif available_mb > 50:
                self.validation_results.append(
                    f"⚠️ Storage Space: {available_mb:.1f}MB available (low)"
                )
                return True
            else:
                self.validation_results.append(
                    f"❌ Storage Space: {available_mb:.1f}MB available (insufficient)"
                )
                return False

        except Exception as e:
            self.validation_results.append(f"⚠️ Storage Space: Cannot check - {str(e)}")
            return True  # Don't fail validation for this

    def test_face_detection(self):
        """Test face detection capability"""
        print("🔍 Testing Face Detection...")

        try:
            # Load face detection cascade
            face_cascade_path = (
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            face_cascade = cv2.CascadeClassifier(face_cascade_path)

            if face_cascade.empty():
                self.validation_results.append(
                    "❌ Face Detection: Haar cascade not loaded"
                )
                return False

            # Try to capture a frame and detect faces
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                    if len(faces) > 0:
                        self.validation_results.append(
                            f"✅ Face Detection: Working ({len(faces)} faces detected)"
                        )
                    else:
                        self.validation_results.append(
                            "⚠️ Face Detection: Working (no faces in current frame)"
                        )

                    cap.release()
                    return True
                else:
                    self.validation_results.append(
                        "❌ Face Detection: Can't capture frame"
                    )
                    cap.release()
                    return False
            else:
                self.validation_results.append("❌ Face Detection: Can't access camera")
                return False

        except Exception as e:
            self.validation_results.append(f"❌ Face Detection: Error - {str(e)}")
            return False

    def create_collection_guide(self):
        """Create a guide for data collection"""
        guide_content = f"""
# 📸 PANDUAN PENGUMPULAN DATA WAJAH

## Persiapan:
- Pastikan pencahayaan cukup terang
- Posisi kamera setinggi mata
- Background relatif polos
- Jarak optimal: 50-100cm dari kamera

## Proses Pengumpulan:
1. Jalankan: `python take_pics.py`
2. Masukkan nama karyawan (gunakan format konsisten)
3. Ambil 30-50 foto dengan variasi:
   - Menghadap lurus ke kamera
   - Sedikit menoleh kiri/kanan (±15°)
   - Sedikit menunduk/mendongak (±10°)
   - Dengan/tanpa kacamata (jika biasa pakai)
   - Ekspresi normal dan senyum

## Tips Kualitas Data:
✅ DO:
- Pastikan wajah terlihat jelas
- Variasi pose ringan
- Pencahayaan konsisten
- Mata terbuka dan terlihat
- Minimal 30 foto per orang

❌ DON'T:
- Foto blur atau gelap
- Wajah tertutup tangan/masker
- Pose ekstrem (>30° rotasi)
- Background berubah drastis
- Kurang dari 20 foto

## Setelah Pengumpulan:
1. Jalankan: `python train_faces.py`
2. Test dengan: `python take_attendance_touchscreen.py`

## Validasi Terakhir: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        guide_file = self.base_dir / "DATA_COLLECTION_GUIDE.md"
        with open(guide_file, "w", encoding="utf-8") as file:
            file.write(guide_content)

        print(f"✅ Panduan pengumpulan data dibuat: {guide_file.name}")

    def run_validation(self):
        """Run complete validation"""
        print("🔍 PRE-COLLECTION SYSTEM VALIDATION")
        print("=" * 50)

        checks = [
            self.check_opencv_installation,
            self.check_python_dependencies,
            self.check_directory_structure,
            self.check_required_scripts,
            self.check_attendance_file_format,
            self.check_storage_space,
            self.test_face_detection,
        ]

        passed_checks = 0
        total_checks = len(checks)

        for check in checks:
            try:
                if check():
                    passed_checks += 1
            except Exception as e:
                self.validation_results.append(
                    f"❌ {check.__name__}: Exception - {str(e)}"
                )

        # Display results
        print("\n📋 HASIL VALIDASI:")
        print("-" * 30)
        for result in self.validation_results:
            print(f"  {result}")

        print(f"\n📊 SKOR VALIDASI: {passed_checks}/{total_checks}")

        # Generate collection guide
        self.create_collection_guide()

        # Final assessment
        if passed_checks == total_checks:
            print("\n🎉 SISTEM SIAP UNTUK PENGUMPULAN DATA!")
            print("Jalankan: python take_pics.py")
            return True
        elif passed_checks >= total_checks * 0.8:  # 80% pass rate
            print("\n⚠️ SISTEM HAMPIR SIAP")
            print("Perbaiki item yang bermasalah sebelum melanjutkan")
            return False
        else:
            print("\n❌ SISTEM BELUM SIAP")
            print("Perbaiki semua masalah sebelum mengumpulkan data")
            return False


def main():
    """Main function"""
    validator = PreCollectionValidator()

    print("🚀 Memvalidasi kesiapan sistem untuk pengumpulan data...")
    print("Pastikan kamera terhubung dan tidak digunakan aplikasi lain\n")

    is_ready = validator.run_validation()

    if is_ready:
        print("\n✅ Validasi selesai - Sistem siap!")
        print("📖 Baca DATA_COLLECTION_GUIDE.md untuk panduan detail")
    else:
        print("\n❌ Validasi selesai - Perlu perbaikan")
        print("Perbaiki masalah yang ditemukan dan jalankan validasi lagi")


if __name__ == "__main__":
    main()
