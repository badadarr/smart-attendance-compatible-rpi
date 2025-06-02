#!/usr/bin/env python3
"""
Migration script to update existing CSV files to include WORK_HOURS column
"""

import csv
import os
from pathlib import Path
from datetime import datetime, timedelta
import shutil


def calculate_work_hours_from_records(records, name, date):
    """Calculate work hours for a person on a specific date"""
    person_records = [r for r in records if r["NAME"] == name and r["DATE"] == date]

    # Sort by time
    person_records.sort(key=lambda x: x["TIME"])

    total_hours = 0.0
    clock_in_time = None

    for record in person_records:
        if record["STATUS"] == "Clock In":
            if clock_in_time is None:  # First clock in of the day
                clock_in_time = datetime.strptime(record["TIME"], "%H:%M:%S").time()
        elif record["STATUS"] == "Clock Out" and clock_in_time is not None:
            clock_out_time = datetime.strptime(record["TIME"], "%H:%M:%S").time()

            # Calculate hours worked
            clock_in_datetime = datetime.combine(datetime.today(), clock_in_time)
            clock_out_datetime = datetime.combine(datetime.today(), clock_out_time)

            # Handle case where clock out is next day (shouldn't happen but just in case)
            if clock_out_datetime < clock_in_datetime:
                clock_out_datetime += timedelta(days=1)

            hours_worked = (
                clock_out_datetime - clock_in_datetime
            ).total_seconds() / 3600
            total_hours += hours_worked
            clock_in_time = None  # Reset for next session

    return f"{total_hours:.2f}" if total_hours > 0 else ""


def migrate_csv_file(file_path):
    """Migrate a single CSV file to the new format"""
    print(f"Migrating {file_path.name}...")

    # Read existing data
    records = []
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)

    # Check if WORK_HOURS column already exists
    if records and "WORK_HOURS" in records[0]:
        print(f"  ✅ {file_path.name} already has WORK_HOURS column")
        return

    # Create backup
    backup_path = file_path.parent / "backup" / file_path.name
    backup_path.parent.mkdir(exist_ok=True)
    if not backup_path.exists():
        shutil.copy2(file_path, backup_path)
        print(f"  📦 Backup created: {backup_path}")

    # Process records and add WORK_HOURS
    new_records = []
    processed_entries = set()  # Track processed (name, date, time) combinations

    for record in records:
        name = record["NAME"]
        date = record["DATE"]
        time = record["TIME"]
        status = record["STATUS"]

        # Skip if we've already processed this exact entry
        entry_key = (name, date, time)
        if entry_key in processed_entries:
            continue
        processed_entries.add(entry_key)

        work_hours = ""
        if status == "Clock Out":
            work_hours = calculate_work_hours_from_records(records, name, date)

        new_records.append(
            {
                "NAME": name,
                "TIME": time,
                "DATE": date,
                "STATUS": status,
                "WORK_HOURS": work_hours,
            }
        )

    # Write updated data
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["NAME", "TIME", "DATE", "STATUS", "WORK_HOURS"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_records)

    print(f"  ✅ {file_path.name} migrated successfully")


def main():
    """Main migration function"""
    print("🔄 Starting CSV migration to add WORK_HOURS column...")

    # Get project root
    project_root = Path(__file__).parent.parent
    attendance_dir = project_root / "Attendance"

    if not attendance_dir.exists():
        print("❌ Attendance directory not found")
        return

    # Find all CSV files
    csv_files = list(attendance_dir.glob("*.csv"))

    if not csv_files:
        print("✅ No CSV files found to migrate")
        return

    print(f"📋 Found {len(csv_files)} CSV files to check:")
    for csv_file in csv_files:
        print(f"  - {csv_file.name}")

    print()

    # Migrate each file
    for csv_file in csv_files:
        try:
            migrate_csv_file(csv_file)
        except Exception as e:
            print(f"  ❌ Error migrating {csv_file.name}: {e}")

    print()
    print("✅ Migration completed!")


if __name__ == "__main__":
    main()
