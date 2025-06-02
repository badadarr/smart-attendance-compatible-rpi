#!/usr/bin/env python3
"""
Data Reset Script
Safely cleans and resets all attendance and face recognition data
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import csv


class DataResetManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.attendance_dir = self.base_dir / "Attendance"
        self.backup_dir = self.base_dir / "data_backup"

    def create_backup(self):
        """Create backup of existing data before deletion"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)

        print(f"📁 Creating backup in: {backup_path}")

        files_backed_up = []

        # Backup face recognition data
        face_files = ["faces_data.pkl", "names.pkl"]
        for filename in face_files:
            file_path = self.data_dir / filename
            if file_path.exists():
                backup_file = backup_path / filename
                shutil.copy2(file_path, backup_file)
                files_backed_up.append(filename)
                print(f"✅ Backed up: {filename}")

        # Backup attendance CSV files
        if self.attendance_dir.exists():
            attendance_backup = backup_path / "Attendance"
            attendance_backup.mkdir(exist_ok=True)

            csv_files = list(self.attendance_dir.glob("*.csv"))
            for csv_file in csv_files:
                if not csv_file.name.startswith("Attendance_test_"):  # Skip test files
                    backup_file = attendance_backup / csv_file.name
                    shutil.copy2(csv_file, backup_file)
                    files_backed_up.append(f"Attendance/{csv_file.name}")
                    print(f"✅ Backed up: Attendance/{csv_file.name}")

        if files_backed_up:
            print(f"\n📦 Backup completed! {len(files_backed_up)} files backed up")
            return backup_path
        else:
            print("ℹ️  No files found to backup")
            return None

    def clean_face_data(self):
        """Remove face recognition training data"""
        print("\n🧹 Cleaning face recognition data...")

        face_files = ["faces_data.pkl", "names.pkl"]
        cleaned_files = []

        for filename in face_files:
            file_path = self.data_dir / filename
            if file_path.exists():
                file_path.unlink()
                cleaned_files.append(filename)
                print(f"🗑️  Deleted: {filename}")

        if cleaned_files:
            print(f"✅ Cleaned {len(cleaned_files)} face data files")
        else:
            print("ℹ️  No face data files found")

        return len(cleaned_files)

    def clean_attendance_data(self, keep_test_data=True):
        """Remove attendance CSV files"""
        print("\n🧹 Cleaning attendance data...")

        if not self.attendance_dir.exists():
            print("ℹ️  No attendance directory found")
            return 0

        csv_files = list(self.attendance_dir.glob("*.csv"))
        cleaned_files = []

        for csv_file in csv_files:
            # Keep test data if requested
            if keep_test_data and csv_file.name.startswith("Attendance_test_"):
                print(f"⏭️  Keeping test file: {csv_file.name}")
                continue

            csv_file.unlink()
            cleaned_files.append(csv_file.name)
            print(f"🗑️  Deleted: {csv_file.name}")

        if cleaned_files:
            print(f"✅ Cleaned {len(cleaned_files)} attendance files")
        else:
            print("ℹ️  No attendance files found to clean")

        return len(cleaned_files)

    def reset_all_data(self, create_backup_first=True):
        """Reset all data with optional backup"""
        print("🚀 Starting data reset process...")
        print("=" * 50)

        backup_path = None
        if create_backup_first:
            backup_path = self.create_backup()

        # Clean data
        face_files_cleaned = self.clean_face_data()
        attendance_files_cleaned = self.clean_attendance_data()

        print("\n📊 Reset Summary:")
        print(f"   Face data files cleaned: {face_files_cleaned}")
        print(f"   Attendance files cleaned: {attendance_files_cleaned}")

        if backup_path:
            print(f"   Backup created at: {backup_path}")

        print("\n✅ Data reset completed!")

        return {
            "backup_path": backup_path,
            "face_files_cleaned": face_files_cleaned,
            "attendance_files_cleaned": attendance_files_cleaned,
        }

    def list_backups(self):
        """List available backups"""
        if not self.backup_dir.exists():
            print("📁 No backup directory found")
            return []

        backups = [d for d in self.backup_dir.iterdir() if d.is_dir()]
        backups.sort(reverse=True)  # Most recent first

        if backups:
            print("📦 Available backups:")
            for i, backup in enumerate(backups, 1):
                backup_time = datetime.strptime(backup.name, "%Y%m%d_%H%M%S")
                formatted_time = backup_time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"   {i}. {backup.name} ({formatted_time})")
        else:
            print("📁 No backups found")

        return backups

    def restore_backup(self, backup_name):
        """Restore data from a specific backup"""
        backup_path = self.backup_dir / backup_name

        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_name}")
            return False

        print(f"🔄 Restoring from backup: {backup_name}")

        # Restore face data
        face_files = ["faces_data.pkl", "names.pkl"]
        for filename in face_files:
            backup_file = backup_path / filename
            if backup_file.exists():
                target_file = self.data_dir / filename
                shutil.copy2(backup_file, target_file)
                print(f"✅ Restored: {filename}")

        # Restore attendance data
        attendance_backup = backup_path / "Attendance"
        if attendance_backup.exists():
            self.attendance_dir.mkdir(exist_ok=True)

            for csv_file in attendance_backup.glob("*.csv"):
                target_file = self.attendance_dir / csv_file.name
                shutil.copy2(csv_file, target_file)
                print(f"✅ Restored: Attendance/{csv_file.name}")

        print("✅ Restore completed!")
        return True


def print_data_collection_guide():
    """Print guide for collecting new face data"""
    print("\n" + "=" * 60)
    print("📚 PANDUAN MENGUMPULKAN DATA WAJAH BARU")
    print("=" * 60)

    print("\n🎯 Langkah-langkah:")
    print("1. Pastikan kamera sudah terpasang dan berfungsi")
    print("2. Jalankan script pengumpulan data:")
    print("   python add_faces_rpi.py")

    print("\n📸 Tips untuk foto yang baik:")
    print("• Pastikan pencahayaan cukup terang")
    print("• Wajah menghadap langsung ke kamera")
    print("• Jarak sekitar 50-100 cm dari kamera")
    print("• Hindari bayangan di wajah")
    print("• Ambil dari berbagai sudut sedikit (depan, sedikit kiri/kanan)")

    print("\n👥 Untuk setiap orang:")
    print("• Ambil minimal 30-50 foto")
    print("• Pastikan nama dieja dengan benar")
    print("• Gunakan nama yang konsisten")

    print("\n✅ Setelah selesai:")
    print("• Jalankan sistem absensi: python take_attendance_touchscreen.py")
    print("• Test recognition dengan semua orang yang terdaftar")

    print("\n🔧 Script yang tersedia:")
    print("• add_faces_rpi.py - Mengumpulkan data wajah")
    print("• take_attendance_touchscreen.py - Sistem absensi touchscreen")
    print("• attendance_reports.py - Membuat laporan")
    print("• reset_data.py - Reset data (script ini)")


def main():
    """Main reset interface"""
    manager = DataResetManager()

    print("🔄 Data Reset Manager")
    print("=" * 30)
    print("⚠️  PERINGATAN: Operasi ini akan menghapus data!")
    print("Pastikan Anda sudah membackup data penting.")
    print()
    print("Pilihan:")
    print("1. Reset semua data (dengan backup)")
    print("2. Reset semua data (tanpa backup)")
    print("3. Hapus hanya data wajah")
    print("4. Hapus hanya data absensi")
    print("5. Lihat backup yang tersedia")
    print("6. Restore dari backup")
    print("7. Panduan mengumpulkan data baru")
    print("8. Keluar")

    choice = input("\nPilih opsi (1-8): ").strip()

    if choice == "1":
        print(
            "\n⚠️  Ini akan menghapus SEMUA data dengan membuat backup terlebih dahulu"
        )
        confirm = input("Apakah Anda yakin? (ketik 'YAKIN' untuk konfirmasi): ").strip()
        if confirm == "YAKIN":
            result = manager.reset_all_data(create_backup_first=True)
            print_data_collection_guide()
        else:
            print("❌ Reset dibatalkan")

    elif choice == "2":
        print("\n⚠️  Ini akan menghapus SEMUA data TANPA backup!")
        confirm = input(
            "Apakah Anda BENAR-BENAR yakin? (ketik 'YAKIN SEKALI' untuk konfirmasi): "
        ).strip()
        if confirm == "YAKIN SEKALI":
            result = manager.reset_all_data(create_backup_first=False)
            print_data_collection_guide()
        else:
            print("❌ Reset dibatalkan")

    elif choice == "3":
        print("\n⚠️  Ini akan menghapus data wajah (faces_data.pkl, names.pkl)")
        confirm = input("Apakah Anda yakin? (y/n): ").strip().lower()
        if confirm == "y":
            manager.clean_face_data()
            print(
                "\n📚 Sekarang jalankan 'python add_faces_rpi.py' untuk mengumpulkan data wajah baru"
            )
        else:
            print("❌ Operasi dibatalkan")

    elif choice == "4":
        print("\n⚠️  Ini akan menghapus semua file absensi CSV")
        confirm = input("Apakah Anda yakin? (y/n): ").strip().lower()
        if confirm == "y":
            manager.clean_attendance_data()
        else:
            print("❌ Operasi dibatalkan")

    elif choice == "5":
        manager.list_backups()

    elif choice == "6":
        backups = manager.list_backups()
        if backups:
            try:
                backup_num = int(input("\nPilih nomor backup untuk restore: ")) - 1
                if 0 <= backup_num < len(backups):
                    manager.restore_backup(backups[backup_num].name)
                else:
                    print("❌ Nomor backup tidak valid")
            except ValueError:
                print("❌ Input tidak valid")
        else:
            print("❌ Tidak ada backup yang tersedia")

    elif choice == "7":
        print_data_collection_guide()

    elif choice == "8":
        print("👋 Terima kasih!")

    else:
        print("❌ Pilihan tidak valid")


if __name__ == "__main__":
    main()
