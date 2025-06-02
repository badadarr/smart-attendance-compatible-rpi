#!/usr/bin/env python3
"""
Attendance Reports Generator with Clock In/Clock Out Analysis
Generates detailed reports with work hours calculations
"""

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

class AttendanceReportGenerator:
    def __init__(self, attendance_dir="Attendance"):
        self.attendance_dir = Path(attendance_dir)
        
    def calculate_daily_hours(self, records):
        """Calculate work hours for a single day's records"""
        if len(records) < 2:
            return 0.0
        
        total_hours = 0.0
        clock_in_time = None
        
        for record in records:
            status = record["STATUS"]
            time_str = record["TIME"]
            
            try:
                record_time = datetime.strptime(time_str, "%H:%M:%S").time()
                
                if status in ["Clock In", "Present"]:
                    clock_in_time = record_time
                elif status == "Clock Out" and clock_in_time:
                    # Calculate hours between clock in and clock out
                    clock_in_datetime = datetime.combine(datetime.today(), clock_in_time)
                    clock_out_datetime = datetime.combine(datetime.today(), record_time)
                    
                    hours_worked = (clock_out_datetime - clock_in_datetime).total_seconds() / 3600
                    total_hours += hours_worked
                    clock_in_time = None
                    
            except ValueError:
                continue
        
        return round(total_hours, 2)
    
    def format_hours(self, hours):
        """Format hours as HH:MM"""
        if hours <= 0:
            return "00:00"
        
        hours_int = int(hours)
        minutes = int((hours - hours_int) * 60)
        return f"{hours_int:02d}:{minutes:02d}"
    
    def get_daily_report(self, date_str):
        """Generate daily attendance report"""
        attendance_file = self.attendance_dir / f"Attendance_{date_str}.csv"
        
        if not attendance_file.exists():
            return None
        
        daily_summary = {}
        
        try:
            with open(attendance_file, 'r') as f:
                reader = csv.DictReader(f)
                
                # Group records by person
                person_records = {}
                for row in reader:
                    name = row["NAME"]
                    if name not in person_records:
                        person_records[name] = []
                    person_records[name].append(row)
                
                # Calculate summary for each person
                for name, records in person_records.items():
                    # Sort records by time
                    records.sort(key=lambda x: x["TIME"])
                    
                    work_hours = self.calculate_daily_hours(records)
                    
                    # Get first and last record times
                    first_record = records[0]
                    last_record = records[-1]
                    
                    daily_summary[name] = {
                        "first_entry": first_record["TIME"],
                        "first_status": first_record["STATUS"],
                        "last_entry": last_record["TIME"],
                        "last_status": last_record["STATUS"],
                        "total_hours": work_hours,
                        "total_hours_formatted": self.format_hours(work_hours),
                        "total_records": len(records),
                        "records": records
                    }
                    
        except Exception as e:
            print(f"Error processing daily report: {e}")
            return None
        
        return daily_summary
    
    def get_weekly_report(self, start_date_str):
        """Generate weekly attendance report"""
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        weekly_summary = {}
        
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            
            daily_data = self.get_daily_report(date_str)
            if daily_data:
                for name, data in daily_data.items():
                    if name not in weekly_summary:
                        weekly_summary[name] = {
                            "days_worked": 0,
                            "total_hours": 0.0,
                            "daily_breakdown": {}
                        }
                    
                    weekly_summary[name]["days_worked"] += 1
                    weekly_summary[name]["total_hours"] += data["total_hours"]
                    weekly_summary[name]["daily_breakdown"][date_str] = data
        
        # Format total hours for each person
        for name in weekly_summary:
            total_hours = weekly_summary[name]["total_hours"]
            weekly_summary[name]["total_hours_formatted"] = self.format_hours(total_hours)
        
        return weekly_summary
    
    def export_daily_report_csv(self, date_str, output_file=None):
        """Export daily report to CSV with work hours"""
        daily_data = self.get_daily_report(date_str)
        
        if not daily_data:
            print(f"No data found for {date_str}")
            return False
        
        if output_file is None:
            output_file = f"Daily_Report_{date_str}.csv"
        
        try:
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "NAME", "FIRST_ENTRY", "FIRST_STATUS", 
                    "LAST_ENTRY", "LAST_STATUS", "WORK_HOURS", 
                    "TOTAL_RECORDS"
                ])
                
                # Write data
                for name, data in daily_data.items():
                    writer.writerow([
                        name,
                        data["first_entry"],
                        data["first_status"],
                        data["last_entry"],
                        data["last_status"],
                        data["total_hours_formatted"],
                        data["total_records"]
                    ])
            
            print(f"Daily report exported to: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error exporting daily report: {e}")
            return False
    
    def export_weekly_report_csv(self, start_date_str, output_file=None):
        """Export weekly report to CSV"""
        weekly_data = self.get_weekly_report(start_date_str)
        
        if not weekly_data:
            print(f"No data found for week starting {start_date_str}")
            return False
        
        if output_file is None:
            output_file = f"Weekly_Report_{start_date_str}.csv"
        
        try:
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "NAME", "DAYS_WORKED", "TOTAL_HOURS", "AVERAGE_HOURS_PER_DAY"
                ])
                
                # Write data
                for name, data in weekly_data.items():
                    avg_hours = data["total_hours"] / max(data["days_worked"], 1)
                    writer.writerow([
                        name,
                        data["days_worked"],
                        data["total_hours_formatted"],
                        self.format_hours(avg_hours)
                    ])
            
            print(f"Weekly report exported to: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error exporting weekly report: {e}")
            return False
    
    def print_daily_summary(self, date_str):
        """Print formatted daily summary to console"""
        daily_data = self.get_daily_report(date_str)
        
        if not daily_data:
            print(f"❌ No attendance data found for {date_str}")
            return
        
        print(f"\n📊 Daily Attendance Report - {date_str}")
        print("=" * 60)
        
        for name, data in daily_data.items():
            print(f"\n👤 {name}")
            print(f"   First Entry: {data['first_entry']} ({data['first_status']})")
            print(f"   Last Entry:  {data['last_entry']} ({data['last_status']})")
            print(f"   Work Hours:  {data['total_hours_formatted']}")
            print(f"   Records:     {data['total_records']}")
            
            # Show all records
            print("   Timeline:")
            for record in data['records']:
                print(f"     {record['TIME']} - {record['STATUS']}")
    
    def print_weekly_summary(self, start_date_str):
        """Print formatted weekly summary to console"""
        weekly_data = self.get_weekly_report(start_date_str)
        
        if not weekly_data:
            print(f"❌ No attendance data found for week starting {start_date_str}")
            return
        
        print(f"\n📈 Weekly Attendance Report - Week of {start_date_str}")
        print("=" * 60)
        
        for name, data in weekly_data.items():
            print(f"\n👤 {name}")
            print(f"   Days Worked:   {data['days_worked']}/7")
            print(f"   Total Hours:   {data['total_hours_formatted']}")
            
            avg_hours = data["total_hours"] / max(data["days_worked"], 1)
            print(f"   Average/Day:   {self.format_hours(avg_hours)}")
            
            print("   Daily Breakdown:")
            for date_str, day_data in data['daily_breakdown'].items():
                print(f"     {date_str}: {day_data['total_hours_formatted']}")


def main():
    """Example usage"""
    generator = AttendanceReportGenerator()
    
    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")
    
    print("🎯 Attendance Report Generator")
    print("=" * 40)
    print("1. Daily Report")
    print("2. Weekly Report") 
    print("3. Export Daily CSV")
    print("4. Export Weekly CSV")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        date = input(f"Enter date (YYYY-MM-DD) or press Enter for today [{today}]: ").strip()
        if not date:
            date = today
        generator.print_daily_summary(date)
        
    elif choice == "2":
        date = input(f"Enter start date (YYYY-MM-DD) or press Enter for this week [{today}]: ").strip()
        if not date:
            date = today
        generator.print_weekly_summary(date)
        
    elif choice == "3":
        date = input(f"Enter date (YYYY-MM-DD) or press Enter for today [{today}]: ").strip()
        if not date:
            date = today
        generator.export_daily_report_csv(date)
        
    elif choice == "4":
        date = input(f"Enter start date (YYYY-MM-DD) or press Enter for this week [{today}]: ").strip()
        if not date:
            date = today
        generator.export_weekly_report_csv(date)
    
    else:
        print("Invalid option selected")


if __name__ == "__main__":
    main()
