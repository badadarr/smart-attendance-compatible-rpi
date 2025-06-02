#!/usr/bin/env python3
"""
Demo Clock In/Clock Out System
Simulasi penggunaan sistem absensi dengan clock in/clock out
"""

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
import time


class ClockInOutDemo:
    def __init__(self):
        self.attendance_dir = Path("Attendance")
        self.attendance_dir.mkdir(exist_ok=True)
        self.demo_date = datetime.now().strftime("%Y-%m-%d")

    def simulate_employee_day(self, name, scenarios="normal"):
        """Simulasi satu hari kerja karyawan"""
        print(f"\n👤 Simulasi hari kerja: {name}")
        print("-" * 40)

        if scenarios == "normal":
            # Hari kerja normal: 9:00-17:00
            times = [("09:00:00", "Clock In"), ("17:00:00", "Clock Out")]
        elif scenarios == "with_lunch":
            # Dengan lunch break: 9:00-12:00, 13:00-17:00
            times = [
                ("09:00:00", "Clock In"),
                ("12:00:00", "Clock Out"),  # Lunch break start
                ("13:00:00", "Clock In"),  # Lunch break end
                ("17:00:00", "Clock Out"),
            ]
        elif scenarios == "overtime":
            # Overtime: 8:00-19:00
            times = [("08:00:00", "Clock In"), ("19:00:00", "Clock Out")]
        elif scenarios == "half_day":
            # Half day: 9:00-13:00
            times = [("09:00:00", "Clock In"), ("13:00:00", "Clock Out")]
        elif scenarios == "shift_work":
            # Shift malam: 22:00-06:00 (next day)
            times = [
                ("22:00:00", "Clock In"),
                ("06:00:00", "Clock Out"),  # Simplified for demo
            ]

        records = []
        total_hours = 0.0
        clock_in_time = None

        for time_str, status in times:
            # Simpan record
            record = {
                "NAME": name,
                "TIME": time_str,
                "DATE": self.demo_date,
                "STATUS": status,
            }

            # Hitung jam kerja
            if status == "Clock In":
                clock_in_time = datetime.strptime(time_str, "%H:%M:%S").time()
                work_hours_str = self.format_hours(total_hours)
            elif status == "Clock Out" and clock_in_time:
                clock_out_time = datetime.strptime(time_str, "%H:%M:%S").time()

                # Hitung durasi
                clock_in_dt = datetime.combine(datetime.today(), clock_in_time)
                clock_out_dt = datetime.combine(datetime.today(), clock_out_time)
                duration = (clock_out_dt - clock_in_dt).total_seconds() / 3600
                total_hours += duration
                work_hours_str = self.format_hours(total_hours)
                clock_in_time = None

            record["WORK_HOURS"] = work_hours_str
            records.append(record)

            # Print real-time
            print(f"⏰ {time_str} - {status} | Total: {work_hours_str}")
            time.sleep(0.5)  # Simulasi delay

        return records

    def format_hours(self, hours):
        """Format jam kerja ke HH:MM"""
        if hours <= 0:
            return "00:00"
        hours_int = int(hours)
        minutes = int((hours - hours_int) * 60)
        return f"{hours_int:02d}:{minutes:02d}"

    def save_demo_data(self, all_records):
        """Simpan data demo ke CSV"""
        demo_file = self.attendance_dir / f"Attendance_demo_{self.demo_date}.csv"

        with open(demo_file, "w", newline="") as f:
            fieldnames = ["NAME", "TIME", "DATE", "STATUS", "WORK_HOURS"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)

        print(f"\n💾 Data demo disimpan: {demo_file}")
        return demo_file

    def generate_demo_report(self, demo_file):
        """Generate laporan dari data demo"""
        print(f"\n📊 LAPORAN ABSENSI DEMO - {self.demo_date}")
        print("=" * 60)

        # Read data
        with open(demo_file, "r") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        # Group by employee
        employees = {}
        for record in records:
            name = record["NAME"]
            if name not in employees:
                employees[name] = []
            employees[name].append(record)

        # Generate report for each employee
        for name, emp_records in employees.items():
            print(f"\n👤 {name}")
            print(
                f"   Jam Masuk Pertama: {emp_records[0]['TIME']} ({emp_records[0]['STATUS']})"
            )
            print(
                f"   Jam Keluar Terakhir: {emp_records[-1]['TIME']} ({emp_records[-1]['STATUS']})"
            )
            print(f"   Total Jam Kerja: {emp_records[-1]['WORK_HOURS']}")
            print(f"   Jumlah Record: {len(emp_records)}")

            print("   Timeline Lengkap:")
            for record in emp_records:
                print(
                    f"     {record['TIME']} - {record['STATUS']} (Total: {record['WORK_HOURS']})"
                )

    def run_demo(self):
        """Jalankan demo lengkap"""
        print("🎯 DEMO SISTEM CLOCK IN/CLOCK OUT")
        print("=" * 50)
        print("Simulasi berbagai skenario kerja karyawan")

        all_records = []

        # Demo berbagai skenario
        scenarios = [
            ("Alice", "normal", "Hari kerja normal 9-17"),
            ("Bob", "with_lunch", "Dengan lunch break"),
            ("Charlie", "overtime", "Overtime 8-19"),
            ("Diana", "half_day", "Half day 9-13"),
            ("Eve", "shift_work", "Shift kerja"),
        ]

        for name, scenario, description in scenarios:
            print(f"\n🎬 Skenario: {description}")
            records = self.simulate_employee_day(name, scenario)
            all_records.extend(records)

        # Simpan dan generate report
        demo_file = self.save_demo_data(all_records)
        self.generate_demo_report(demo_file)

        # Summary
        print(f"\n🎉 DEMO SELESAI!")
        print(f"📁 File demo: {demo_file}")
        print("\n🔧 Untuk menggunakan sistem yang sesungguhnya:")
        print("1. python take_attendance_touchscreen.py")
        print("2. python attendance_reports.py")
        print("3. python migrate_attendance_data.py")

        return demo_file


def main():
    """Main demo function"""
    demo = ClockInOutDemo()

    print("Apakah Anda ingin menjalankan demo? (y/n): ", end="")
    choice = input().strip().lower()

    if choice == "y":
        demo_file = demo.run_demo()

        print("\nApakah Anda ingin melihat struktur file CSV? (y/n): ", end="")
        if input().strip().lower() == "y":
            print(f"\n📄 Isi file {demo_file}:")
            with open(demo_file, "r") as f:
                print(f.read())
    else:
        print("Demo dibatalkan.")


if __name__ == "__main__":
    main()
