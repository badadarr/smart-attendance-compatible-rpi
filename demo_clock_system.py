#!/usr/bin/env python3
"""
Demo Clock In/Clock Out System Testing
"""

import sys
import os

sys.path.append("src")

from app_touchscreen import WebAttendanceSystem
from datetime import datetime
import csv


def demo_clock_system():
    """Demo the Clock In/Clock Out system with real data"""
    print("🎯 Clock In/Clock Out System Demo")
    print("=" * 50)

    # Initialize system
    system = WebAttendanceSystem()

    # Demo data
    demo_users = ["Alice Johnson", "Bob Smith", "Charlie Brown"]
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"📅 Demo Date: {today}")
    print(f"👥 Demo Users: {', '.join(demo_users)}")
    print()

    # Ensure directory exists
    system.attendance_dir.mkdir(exist_ok=True)

    # Demo scenario: Morning Clock In
    print("🌅 Morning: Users Clock In")
    morning_times = ["08:00:00", "08:15:00", "08:30:00"]

    for user, time in zip(demo_users, morning_times):
        status = system.determine_attendance_status(user, time, today)
        system.save_attendance(user, time, today, status)
        print(f"   {time} - {user}: {status}")

    print()

    # Demo scenario: Lunch Break (some users Clock Out)
    print("🍽️  Lunch: Some users Clock Out")
    lunch_out_times = ["12:00:00", "12:15:00"]
    lunch_users = demo_users[:2]  # Only first two users

    for user, time in zip(lunch_users, lunch_out_times):
        status = system.determine_attendance_status(user, time, today)
        system.save_attendance(user, time, today, status)
        print(f"   {time} - {user}: {status}")

    print()

    # Demo scenario: Return from Lunch
    print("🔄 Afternoon: Users return from lunch")
    lunch_in_times = ["13:00:00", "13:15:00"]

    for user, time in zip(lunch_users, lunch_in_times):
        status = system.determine_attendance_status(user, time, today)
        system.save_attendance(user, time, today, status)
        print(f"   {time} - {user}: {status}")

    print()

    # Demo scenario: End of Day Clock Out
    print("🌆 Evening: All users Clock Out")
    evening_times = ["17:00:00", "17:10:00", "17:05:00"]

    for user, time in zip(demo_users, evening_times):
        status = system.determine_attendance_status(user, time, today)
        system.save_attendance(user, time, today, status)
        print(f"   {time} - {user}: {status}")

    print()
    print("=" * 50)

    # Show final attendance records
    print("📊 Final Attendance Summary:")
    attendance_file = system.attendance_dir / f"Attendance_{today}.csv"

    if attendance_file.exists():
        with open(attendance_file, "r") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        for user in demo_users:
            user_records = [r for r in records if r["NAME"] == user]
            print(f"\n👤 {user}:")
            for record in user_records:
                print(f"   {record['TIME']} - {record['STATUS']}")

    print("\n✅ Demo completed! Check the web dashboard to see the data.")
    print("🌐 Dashboard: http://127.0.0.1:5000")
    print("📱 Touchscreen: http://127.0.0.1:5001")


if __name__ == "__main__":
    demo_clock_system()
