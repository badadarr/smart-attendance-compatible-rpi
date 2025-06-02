#!/usr/bin/env python3
"""
Test Migration Tool
"""

from pathlib import Path
import sys

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from migrate_attendance_data import AttendanceDataMigrator


def test_migration():
    print("🧪 Testing Migration Tool")

    migrator = AttendanceDataMigrator()

    # Test with existing file
    test_file = migrator.attendance_dir / "Attendance_2025-05-29.csv"

    if test_file.exists():
        print(f"✅ Found test file: {test_file}")
        result = migrator.migrate_file(test_file, dry_run=True)
        print(f"Migration result: {result}")
    else:
        print(f"❌ Test file not found: {test_file}")

        # List available files
        files = list(migrator.attendance_dir.glob("Attendance_*.csv"))
        if files:
            print("Available files:")
            for f in files:
                print(f"  {f.name}")
        else:
            print("No attendance files found")


if __name__ == "__main__":
    test_migration()
