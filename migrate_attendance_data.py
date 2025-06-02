#!/usr/bin/env python3
"""
Data Migration Script for Clock In/Clock Out System
Converts old "Present" records to Clock In/Clock Out format
"""

import csv
import os
from datetime import datetime
from pathlib import Path
import shutil


class AttendanceDataMigrator:
    def __init__(self, attendance_dir="Attendance"):
        self.attendance_dir = Path(attendance_dir)
        self.backup_dir = self.attendance_dir / "backup"
        self.backup_dir.mkdir(exist_ok=True)

    def backup_file(self, file_path):
        """Create backup of original file"""
        backup_path = self.backup_dir / f"{file_path.name}.backup"
        shutil.copy2(file_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        return backup_path

    def migrate_file(self, file_path, dry_run=True):
        """Migrate a single attendance file to clock in/clock out format"""
        print(f"\n🔄 Processing: {file_path}")

        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return False

        # Read original data
        try:
            with open(file_path, "r") as f:
                reader = csv.DictReader(f)
                records = list(reader)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False

        if not records:
            print("ℹ️  No records found in file")
            return True

        # Check if already migrated
        if "WORK_HOURS" in records[0].keys():
            print("ℹ️  File already migrated (has WORK_HOURS column)")
            return True

        # Group records by person and process
        person_records = {}
        for record in records:
            name = record["NAME"]
            if name not in person_records:
                person_records[name] = []
            person_records[name].append(record)

        migrated_records = []

        for name, person_data in person_records.items():
            # Sort by time
            person_data.sort(key=lambda x: x["TIME"])

            print(f"  👤 {name}: {len(person_data)} records")

            # Convert Present records to Clock In/Clock Out pattern
            for i, record in enumerate(person_data):
                new_record = record.copy()

                # Determine status based on position and time
                if record["STATUS"] == "Present":
                    # First record of the day should be Clock In
                    if i == 0:
                        new_record["STATUS"] = "Clock In"
                    # Last record should be Clock Out
                    elif i == len(person_data) - 1:
                        new_record["STATUS"] = "Clock Out"
                    # Middle records alternate
                    else:
                        # Check previous record to determine next status
                        prev_status = (
                            migrated_records[-1]["STATUS"]
                            if migrated_records
                            else "Clock Out"
                        )
                        if prev_status == "Clock In":
                            new_record["STATUS"] = "Clock Out"
                        else:
                            new_record["STATUS"] = "Clock In"

                # Calculate work hours (placeholder, will be recalculated)
                new_record["WORK_HOURS"] = "00:00"

                migrated_records.append(new_record)

                status_change = (
                    "→ " + new_record["STATUS"]
                    if new_record["STATUS"] != record["STATUS"]
                    else ""
                )
                print(f"    {record['TIME']} {record['STATUS']} {status_change}")

        # Calculate proper work hours for each record
        self.calculate_work_hours_for_records(migrated_records)

        if dry_run:
            print("\n🔍 DRY RUN - No changes made")
            print("Run with dry_run=False to apply changes")
            return True

        # Create backup before modifying
        self.backup_file(file_path)

        # Write migrated data
        try:
            with open(file_path, "w", newline="") as f:
                fieldnames = ["NAME", "TIME", "DATE", "STATUS", "WORK_HOURS"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(migrated_records)

            print(f"✅ Migration completed: {len(migrated_records)} records processed")
            return True

        except Exception as e:
            print(f"❌ Error writing migrated file: {e}")
            return False

    def calculate_work_hours_for_records(self, records):
        """Calculate and update work hours for all records"""
        # Group by person and date
        person_date_records = {}

        for record in records:
            key = (record["NAME"], record["DATE"])
            if key not in person_date_records:
                person_date_records[key] = []
            person_date_records[key].append(record)

        # Calculate work hours for each person-date group
        for (name, date), day_records in person_date_records.items():
            day_records.sort(key=lambda x: x["TIME"])

            total_hours = 0.0
            clock_in_time = None

            for record in day_records:
                status = record["STATUS"]
                time_str = record["TIME"]

                try:
                    record_time = datetime.strptime(time_str, "%H:%M:%S").time()

                    if status == "Clock In":
                        clock_in_time = record_time
                    elif status == "Clock Out" and clock_in_time:
                        # Calculate hours between clock in and clock out
                        clock_in_datetime = datetime.combine(
                            datetime.today(), clock_in_time
                        )
                        clock_out_datetime = datetime.combine(
                            datetime.today(), record_time
                        )

                        hours_worked = (
                            clock_out_datetime - clock_in_datetime
                        ).total_seconds() / 3600
                        total_hours += hours_worked
                        clock_in_time = None

                    # Update record with cumulative work hours
                    hours_int = int(total_hours)
                    minutes = int((total_hours - hours_int) * 60)
                    record["WORK_HOURS"] = f"{hours_int:02d}:{minutes:02d}"

                except ValueError:
                    record["WORK_HOURS"] = "00:00"

    def migrate_all_files(self, dry_run=True):
        """Migrate all attendance files in the directory"""
        print("🚀 Starting attendance data migration...")
        print(f"📁 Attendance directory: {self.attendance_dir}")

        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        else:
            print("⚠️  LIVE MODE - Files will be modified")
            confirm = (
                input("Are you sure you want to proceed? (yes/no): ").strip().lower()
            )
            if confirm != "yes":
                print("❌ Migration cancelled")
                return False

        attendance_files = list(self.attendance_dir.glob("Attendance_*.csv"))

        if not attendance_files:
            print("❌ No attendance files found")
            return False

        print(f"📊 Found {len(attendance_files)} attendance files")

        success_count = 0
        for file_path in attendance_files:
            if self.migrate_file(file_path, dry_run=dry_run):
                success_count += 1

        print(f"\n✅ Migration summary:")
        print(f"   Files processed: {len(attendance_files)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {len(attendance_files) - success_count}")

        if not dry_run and success_count > 0:
            print(f"📁 Backups created in: {self.backup_dir}")

        return success_count == len(attendance_files)

    def restore_from_backup(self, date_str):
        """Restore a file from backup"""
        backup_file = self.backup_dir / f"Attendance_{date_str}.csv.backup"
        original_file = self.attendance_dir / f"Attendance_{date_str}.csv"

        if not backup_file.exists():
            print(f"❌ Backup file not found: {backup_file}")
            return False

        try:
            shutil.copy2(backup_file, original_file)
            print(f"✅ Restored from backup: {original_file}")
            return True
        except Exception as e:
            print(f"❌ Error restoring from backup: {e}")
            return False


def main():
    """Main migration interface"""
    migrator = AttendanceDataMigrator()

    print("🔄 Attendance Data Migration Tool")
    print("=" * 50)
    print("This tool converts old 'Present' records to Clock In/Clock Out format")
    print("1. Dry run (preview changes)")
    print("2. Migrate all files")
    print("3. Migrate specific file")
    print("4. Restore from backup")
    print("5. List backup files")

    choice = input("\nSelect option (1-5): ").strip()

    if choice == "1":
        print("\n🔍 Starting dry run...")
        migrator.migrate_all_files(dry_run=True)

    elif choice == "2":
        print("\n⚠️  This will modify your attendance files!")
        migrator.migrate_all_files(dry_run=False)

    elif choice == "3":
        date = input("Enter date (YYYY-MM-DD): ").strip()
        file_path = migrator.attendance_dir / f"Attendance_{date}.csv"

        dry_run = input("Dry run? (y/n): ").strip().lower() == "y"
        migrator.migrate_file(file_path, dry_run=dry_run)

    elif choice == "4":
        date = input("Enter date to restore (YYYY-MM-DD): ").strip()
        migrator.restore_from_backup(date)

    elif choice == "5":
        backup_files = list(migrator.backup_dir.glob("*.backup"))
        if backup_files:
            print(f"\n📁 Backup files in {migrator.backup_dir}:")
            for backup_file in backup_files:
                print(f"   {backup_file.name}")
        else:
            print("No backup files found")

    else:
        print("Invalid option selected")


if __name__ == "__main__":
    main()
