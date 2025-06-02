#!/usr/bin/env python3
"""
Setup Fresh System for Raspberry Pi
Script untuk membersihkan data lama dan mempersiapkan sistem untuk pengumpulan data baru
"""

import os
import shutil
import csv
from datetime import datetime
from pathlib import Path
import logging


class FreshSystemSetup:
    def __init__(self):
        """Initialize fresh system setup"""
        self.base_dir = Path(".")
        self.faces_dir = self.base_dir / "faces"
        self.attendance_dir = self.base_dir / "Attendance"
        self.trainer_dir = self.base_dir / "trainer"
        self.backup_dir = self.base_dir / "backup_before_reset"

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("fresh_system_setup.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def create_backup(self):
        """Buat backup dari data yang ada sebelum dihapus"""
        print("\n🔄 Membuat backup data existing...")

        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = self.backup_dir / f"backup_{timestamp}"
        backup_folder.mkdir(exist_ok=True)

        backup_count = 0

        # Backup faces directory
        if self.faces_dir.exists() and any(self.faces_dir.iterdir()):
            shutil.copytree(self.faces_dir, backup_folder / "faces")
            backup_count += len(list(self.faces_dir.glob("**/*")))
            self.logger.info(f"Backup faces directory: {backup_count} files")

        # Backup attendance files
        if self.attendance_dir.exists():
            attendance_files = list(self.attendance_dir.glob("*.csv"))
            if attendance_files:
                (backup_folder / "Attendance").mkdir(exist_ok=True)
                for file in attendance_files:
                    shutil.copy2(file, backup_folder / "Attendance")
                    backup_count += 1
                self.logger.info(
                    f"Backup attendance files: {len(attendance_files)} files"
                )

        # Backup trainer files
        if self.trainer_dir.exists() and any(self.trainer_dir.iterdir()):
            shutil.copytree(self.trainer_dir, backup_folder / "trainer")
            trainer_files = len(list(self.trainer_dir.glob("**/*")))
            backup_count += trainer_files
            self.logger.info(f"Backup trainer files: {trainer_files} files")

        print(f"✅ Backup selesai: {backup_count} files disimpan di {backup_folder}")
        return backup_folder

    def clean_old_data(self):
        """Hapus data lama untuk memulai fresh"""
        print("\n🧹 Membersihkan data lama...")

        cleaned_items = 0

        # Clean faces directory
        if self.faces_dir.exists():
            shutil.rmtree(self.faces_dir)
            cleaned_items += 1
            self.logger.info("Removed faces directory")

        # Clean attendance files
        if self.attendance_dir.exists():
            attendance_files = list(self.attendance_dir.glob("*.csv"))
            for file in attendance_files:
                file.unlink()
                cleaned_items += 1
            self.logger.info(f"Removed {len(attendance_files)} attendance files")

        # Clean trainer files
        if self.trainer_dir.exists():
            trainer_files = list(self.trainer_dir.glob("**/*"))
            if trainer_files:
                shutil.rmtree(self.trainer_dir)
                cleaned_items += 1
                self.logger.info("Removed trainer directory")

        # Clean any pickle files
        pickle_files = list(self.base_dir.glob("*.pkl"))
        for file in pickle_files:
            file.unlink()
            cleaned_items += 1
            self.logger.info(f"Removed pickle file: {file.name}")

        print(f"✅ Data lama dibersihkan: {cleaned_items} items removed")

    def setup_fresh_directories(self):
        """Buat struktur direktori yang diperlukan"""
        print("\n📁 Membuat struktur direktori fresh...")

        directories = [self.faces_dir, self.attendance_dir, self.trainer_dir]

        created_dirs = 0
        for directory in directories:
            directory.mkdir(exist_ok=True)
            created_dirs += 1
            self.logger.info(f"Created directory: {directory}")

        print(f"✅ Direktori dibuat: {created_dirs} directories")

    def create_initial_attendance_file(self):
        """Buat file attendance kosong dengan header yang benar"""
        print("\n📄 Membuat file attendance template...")

        today = datetime.now().strftime("%Y-%m-%d")
        attendance_file = self.attendance_dir / f"Attendance_{today}.csv"

        # Header untuk clock in/clock out system
        headers = ["NAME", "TIME", "DATE", "STATUS", "WORK_HOURS"]

        with open(attendance_file, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)

        self.logger.info(f"Created initial attendance file: {attendance_file}")
        print(f"✅ File attendance template dibuat: {attendance_file.name}")

    def create_setup_guide(self):
        """Buat panduan langkah selanjutnya"""
        guide_content = f"""
# 🚀 PANDUAN SETUP SISTEM FRESH

## Status Saat Ini:
✅ Data lama telah dibersihkan dan di-backup
✅ Direktori fresh telah dibuat
✅ File attendance template telah disiapkan

## Langkah Selanjutnya:

### 1. Kumpulkan Data Wajah Baru
```bash
python take_pics.py
```
- Masukkan nama karyawan baru
- Ambil 30-50 foto per orang dengan variasi pose dan pencahayaan
- Pastikan kualitas foto baik

### 2. Training Model Face Recognition
```bash
python train_faces.py
```
- Akan membuat model recognizer dari foto yang dikumpulkan
- File trainer.yml akan dibuat di direktori trainer/

### 3. Test Sistem Clock In/Clock Out
```bash
python take_attendance_touchscreen.py
```
- Test clock in dan clock out
- Verifikasi perhitungan work hours
- Cek format CSV attendance

### 4. Validasi Sistem
```bash
python test_clock_system.py
```
- Jalankan test suite untuk memastikan semua fungsi bekerja

### 5. Generate Reports (Opsional)
```bash
python attendance_reports.py
```
- Generate laporan harian/mingguan
- Analisis work hours

## File Yang Tersedia:
- `take_pics.py` - Untuk mengumpulkan foto wajah
- `train_faces.py` - Untuk training model recognition
- `take_attendance_touchscreen.py` - Sistem absensi utama
- `attendance_reports.py` - Generate laporan
- `test_clock_system.py` - Test suite
- `reset_data.py` - Reset data jika diperlukan

## Backup Location:
Data lama telah di-backup di: backup_before_reset/

## Tanggal Setup: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Selamat menggunakan sistem clock in/clock out yang baru! 🎉
"""

        guide_file = self.base_dir / "SETUP_GUIDE.md"
        with open(guide_file, "w", encoding="utf-8") as file:
            file.write(guide_content)

        print(f"✅ Panduan setup dibuat: {guide_file.name}")

    def validate_system_readiness(self):
        """Validasi kesiapan sistem"""
        print("\n🔍 Validasi kesiapan sistem...")

        checks = []

        # Check if required scripts exist
        required_scripts = [
            "take_pics.py",
            "train_faces.py",
            "take_attendance_touchscreen.py",
            "attendance_reports.py",
        ]

        for script in required_scripts:
            if (self.base_dir / script).exists():
                checks.append(f"✅ {script} - Ready")
            else:
                checks.append(f"❌ {script} - Missing")

        # Check directories
        for directory in [self.faces_dir, self.attendance_dir, self.trainer_dir]:
            if directory.exists():
                checks.append(f"✅ {directory.name}/ - Ready")
            else:
                checks.append(f"❌ {directory.name}/ - Missing")

        # Check if directories are empty (should be for fresh start)
        if not any(self.faces_dir.iterdir()) if self.faces_dir.exists() else True:
            checks.append("✅ faces/ - Empty (ready for new data)")
        else:
            checks.append("⚠️ faces/ - Contains data")

        if not any(self.trainer_dir.iterdir()) if self.trainer_dir.exists() else True:
            checks.append("✅ trainer/ - Empty (ready for training)")
        else:
            checks.append("⚠️ trainer/ - Contains data")

        print("\n📋 Status Validasi:")
        for check in checks:
            print(f"  {check}")

        # Count ready items
        ready_count = sum(1 for check in checks if check.startswith("✅"))
        total_count = len(checks)

        print(f"\n📊 Kesiapan Sistem: {ready_count}/{total_count} items ready")

        if ready_count == total_count:
            print("🎉 Sistem siap untuk pengumpulan data baru!")
            return True
        else:
            print("⚠️ Perlu perhatian sebelum melanjutkan")
            return False

    def run_full_setup(self):
        """Jalankan setup lengkap"""
        print("🚀 SETUP FRESH SYSTEM untuk CLOCK IN/CLOCK OUT")
        print("=" * 50)

        try:
            # Step 1: Backup
            backup_location = self.create_backup()

            # Step 2: Clean
            self.clean_old_data()

            # Step 3: Setup fresh directories
            self.setup_fresh_directories()

            # Step 4: Create initial files
            self.create_initial_attendance_file()

            # Step 5: Create guide
            self.create_setup_guide()

            # Step 6: Validate
            is_ready = self.validate_system_readiness()

            print("\n" + "=" * 50)
            print("✅ SETUP SELESAI!")
            print(f"📁 Backup: {backup_location}")
            print("📖 Baca SETUP_GUIDE.md untuk langkah selanjutnya")

            if is_ready:
                print("\n🎯 LANGKAH SELANJUTNYA:")
                print("1. python take_pics.py")
                print("2. python train_faces.py")
                print("3. python take_attendance_touchscreen.py")

            return True

        except Exception as e:
            self.logger.error(f"Setup failed: {str(e)}")
            print(f"❌ Setup gagal: {str(e)}")
            return False


def main():
    """Main function"""
    print("🔧 Fresh System Setup for Clock In/Clock Out")
    print("Apakah Anda yakin ingin membersihkan semua data existing?")
    print("(Data akan di-backup terlebih dahulu)")

    confirm = input("\nKetik 'YES' untuk melanjutkan: ").strip()

    if confirm.upper() == "YES":
        setup = FreshSystemSetup()
        success = setup.run_full_setup()

        if success:
            print("\n🎉 Sistem fresh siap digunakan!")
        else:
            print("\n❌ Setup gagal, periksa log untuk detail")
    else:
        print("❌ Setup dibatalkan")


if __name__ == "__main__":
    main()
