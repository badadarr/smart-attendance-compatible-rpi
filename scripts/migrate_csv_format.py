#!/usr/bin/env python3
"""
CSV Format Migration Script
Mengubah format CSV dari format lama ke format baru yang sederhana

Format Lama: NAME,TIME,DATE,STATUS,WORK_HOURS,CONFIDENCE,QUALITY,FLAGS
Format Baru: NAME,TIME,STATUS

Contoh:
Lama: badar,00:14:50,2025-07-11,Clock In,00:00,1.000,0.511,
Baru: badar,08:00,Clock In
"""

import csv
import os
import shutil
from pathlib import Path
from datetime import datetime


class CSVFormatMigrator:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.attendance_dir = self.base_dir / "Attendance"
        self.backup_dir = self.attendance_dir / "backup_old_format"

        # Format baru yang sederhana
        self.new_columns = ["NAME", "TIME", "STATUS"]

    def create_backup(self):
        """Buat backup file lama"""
        self.backup_dir.mkdir(exist_ok=True)
        print(f"📁 Backup directory: {self.backup_dir}")

    def migrate_file(self, file_path):
        """Migrasi satu file CSV"""
        try:
            print(f"🔄 Migrating: {file_path.name}")

            # Baca file lama
            with open(file_path, "r") as f:
                reader = csv.DictReader(f)
                old_data = list(reader)

            if not old_data:
                print(f"⚠️  File kosong: {file_path.name}")
                return

            # Backup file lama
            backup_file = self.backup_dir / f"{file_path.name}.backup"
            shutil.copy2(file_path, backup_file)
            print(f"💾 Backup saved: {backup_file.name}")

            # Konversi ke format baru
            new_data = []
            for row in old_data:
                new_row = {
                    "NAME": row.get("NAME", "").strip(),
                    "TIME": row.get("TIME", "").strip(),
                    "STATUS": row.get("STATUS", "").strip(),
                }

                # Skip baris kosong
                if new_row["NAME"] and new_row["TIME"] and new_row["STATUS"]:
                    new_data.append(new_row)

            # Tulis file baru
            with open(file_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.new_columns)
                writer.writeheader()
                writer.writerows(new_data)

            print(f"✅ Migrated: {len(new_data)} records")

        except Exception as e:
            print(f"❌ Error migrating {file_path.name}: {e}")

    def migrate_all(self):
        """Migrasi semua file CSV"""
        print("🚀 Starting CSV Format Migration")
        print("=" * 50)

        self.create_backup()

        # Cari semua file attendance
        csv_files = list(self.attendance_dir.glob("Attendance_*.csv"))

        if not csv_files:
            print("⚠️  No attendance files found")
            return

        print(f"📊 Found {len(csv_files)} files to migrate")

        for csv_file in csv_files:
            self.migrate_file(csv_file)

        print("=" * 50)
        print("✅ Migration completed!")
        print(f"📁 Backups saved in: {self.backup_dir}")

    def show_sample(self):
        """Tampilkan contoh format baru"""
        print("\n📋 New CSV Format Sample:")
        print("NAME,TIME,STATUS")
        print("Badar,08:00,Clock In")
        print("Badar,17:00,Clock Out")
        print("John,09:15,Clock In")
        print("John,18:30,Clock Out")


def main():
    migrator = CSVFormatMigrator()

    print("CSV Format Migration Tool")
    print("========================")
    print("This will convert CSV files from old format to new simplified format")
    print("Old: NAME,TIME,DATE,STATUS,WORK_HOURS,CONFIDENCE,QUALITY,FLAGS")
    print("New: NAME,TIME,STATUS")
    print()

    response = input("Continue with migration? (y/N): ").strip().lower()

    if response == "y":
        migrator.migrate_all()
        migrator.show_sample()
    else:
        print("Migration cancelled")


if __name__ == "__main__":
    main()
