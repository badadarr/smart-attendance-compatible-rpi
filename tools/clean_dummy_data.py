#!/usr/bin/env python3
"""
Clean Dummy Data Script
Removes dummy/test data from attendance files and keeps only real attendance records
"""

import os
import csv
import shutil
from pathlib import Path
from datetime import datetime

class DummyDataCleaner:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.attendance_dir = self.base_dir / "Attendance"
        self.backup_dir = self.attendance_dir / "backup"
        
        # Known dummy/test names to remove
        self.dummy_names = {
            "Alice Johnson",
            "Bob Smith", 
            "Charlie Brown",
            "David Wilson",
            "Eva Martinez",
            "Frank Thompson",
            "Grace Lee",
            "Henry Davis",
            "Ivy Chen",
            "Jack Robinson",
            "Test User",
            "Demo User",
            "Sample User",
            "Example User"
        }
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
    def is_dummy_record(self, record):
        """Check if a record contains dummy data"""
        name = record.get('NAME', '').strip()
        
        # Check against known dummy names
        if name in self.dummy_names:
            return True
            
        # Check for test patterns
        name_lower = name.lower()
        test_patterns = ['test', 'demo', 'sample', 'example', 'dummy', 'fake']
        if any(pattern in name_lower for pattern in test_patterns):
            return True
            
        return False
    
    def backup_file(self, file_path):
        """Create backup of original file"""
        backup_path = self.backup_dir / f"{file_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        shutil.copy2(file_path, backup_path)
        print(f"📁 Backup created: {backup_path.name}")
        return backup_path
    
    def clean_attendance_file(self, file_path):
        """Clean dummy data from a single attendance file"""
        if not file_path.exists():
            return False
            
        print(f"\n🔍 Processing: {file_path.name}")
        
        # Read original data
        try:
            with open(file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                original_records = list(reader)
                fieldnames = reader.fieldnames
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")
            return False
        
        if not original_records:
            print(f"📄 File {file_path.name} is empty, skipping")
            return True
            
        # Filter out dummy records
        clean_records = []
        dummy_count = 0
        
        for record in original_records:
            if self.is_dummy_record(record):
                dummy_count += 1
                print(f"🗑️  Removing dummy record: {record.get('NAME', 'Unknown')} - {record.get('TIME', '')} - {record.get('STATUS', '')}")
            else:
                clean_records.append(record)
        
        if dummy_count == 0:
            print(f"✅ No dummy data found in {file_path.name}")
            return True
        
        # Create backup before modifying
        self.backup_file(file_path)
        
        # Write cleaned data
        try:
            with open(file_path, 'w', newline='') as f:
                if clean_records:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(clean_records)
                else:
                    # If no records left, create empty file with headers
                    writer = csv.DictWriter(f, fieldnames=fieldnames or ['NAME', 'TIME', 'DATE', 'STATUS', 'WORK_HOURS', 'CONFIDENCE', 'QUALITY', 'FLAGS'])
                    writer.writeheader()
            
            print(f"✅ Cleaned {file_path.name}: Removed {dummy_count} dummy records, kept {len(clean_records)} real records")
            return True
            
        except Exception as e:
            print(f"❌ Error writing cleaned data to {file_path.name}: {e}")
            return False
    
    def clean_all_files(self):
        """Clean dummy data from all attendance files"""
        print("🧹 Starting dummy data cleanup...")
        print(f"📂 Attendance directory: {self.attendance_dir}")
        print(f"🗑️  Will remove records from these dummy names: {', '.join(sorted(self.dummy_names))}")
        
        # Find all attendance CSV files
        attendance_files = list(self.attendance_dir.glob("Attendance_*.csv"))
        
        if not attendance_files:
            print("📄 No attendance files found")
            return
        
        print(f"📊 Found {len(attendance_files)} attendance files to process")
        
        success_count = 0
        total_files = len(attendance_files)
        
        for file_path in sorted(attendance_files):
            if self.clean_attendance_file(file_path):
                success_count += 1
        
        print(f"\n📈 Cleanup Summary:")
        print(f"   ✅ Successfully processed: {success_count}/{total_files} files")
        print(f"   📁 Backups created in: {self.backup_dir}")
        print(f"   🎯 Real data preserved, dummy data removed")
        
        if success_count == total_files:
            print("\n🎉 Dummy data cleanup completed successfully!")
        else:
            print(f"\n⚠️  Some files had issues. Check the logs above.")
    
    def list_dummy_records(self):
        """List all dummy records without removing them"""
        print("🔍 Scanning for dummy records...")
        
        attendance_files = list(self.attendance_dir.glob("Attendance_*.csv"))
        total_dummy_records = 0
        
        for file_path in sorted(attendance_files):
            if not file_path.exists():
                continue
                
            try:
                with open(file_path, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    records = list(reader)
                
                dummy_records = [r for r in records if self.is_dummy_record(r)]
                
                if dummy_records:
                    print(f"\n📄 {file_path.name}:")
                    for record in dummy_records:
                        print(f"   🗑️  {record.get('NAME', 'Unknown')} - {record.get('TIME', '')} - {record.get('STATUS', '')}")
                    total_dummy_records += len(dummy_records)
                    
            except Exception as e:
                print(f"❌ Error reading {file_path.name}: {e}")
        
        print(f"\n📊 Total dummy records found: {total_dummy_records}")
        return total_dummy_records

def main():
    cleaner = DummyDataCleaner()
    
    print("🧹 Dummy Data Cleaner")
    print("=" * 50)
    
    # First, show what will be removed
    dummy_count = cleaner.list_dummy_records()
    
    if dummy_count == 0:
        print("\n✅ No dummy data found. Your attendance files are clean!")
        return
    
    print(f"\n⚠️  Found {dummy_count} dummy records to remove.")
    
    # Ask for confirmation
    response = input("\n❓ Do you want to proceed with cleanup? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        cleaner.clean_all_files()
    else:
        print("🚫 Cleanup cancelled by user")

if __name__ == "__main__":
    main()