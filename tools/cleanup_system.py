#!/usr/bin/env python3
"""
System Cleanup Script - Immediate Execution
Removes unused files and systems from attendance project
"""
import os
import shutil
from pathlib import Path


def cleanup_system():
    """Run immediate system cleanup"""
    base_dir = Path(__file__).parent
    removed_files = []

    print("🧹 Starting Immediate System Cleanup...")
    print("=" * 50)

    # Files to remove
    files_to_remove = [
        # Touchscreen web system
        "src/app_touchscreen.py",
        "templates/touchscreen_attendance.html",
        "touchscreen_start.sh",
        # Non-touchscreen system
        "src/take_attendance_rpi.py",
        # Unused enhancement and test files
        "test_enhanced.py",
        "test_system_components.py",
        "test_end_to_end.py",
        "test_clock_logic.py",
        "start_enhanced.py",
        "install_enhancements.py",
        "requirements_enhancements.txt",
        "demo_clock_system.py",
        "quick_install.py",
        "migrate_attendance_data.py",
        "attendance_reports.py",
    ]

    # Remove files
    for file_path in files_to_remove:
        full_path = base_dir / file_path
        if full_path.exists():
            full_path.unlink()
            removed_files.append(file_path)
            print(f"🗑️  Removed: {file_path}")
        else:
            print(f"⏭️  Not found: {file_path}")

    print(f"\n✅ Cleanup completed! Removed {len(removed_files)} files")
    print("\n🎯 Remaining core system:")
    print("   📱 Touchscreen Attendance: src/take_attendance_touchscreen.py")
    print("   🌐 Web Dashboard: src/app.py")
    print("   👤 Face Registration: src/add_faces_rpi.py")


if __name__ == "__main__":
    cleanup_system()
