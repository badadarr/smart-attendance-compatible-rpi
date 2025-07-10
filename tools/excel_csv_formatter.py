#!/usr/bin/env python3
"""
Excel CSV Formatter
Utility to create properly structured CSV files for Excel with exact column positioning
"""

import pandas as pd
from datetime import datetime
import os
from pathlib import Path

def create_excel_ready_csv(df, filename_prefix="excel_export", include_summary=True):
    """
    Create Excel-ready CSV with proper column structure:
    A1=NAME, B1=TIME, C1=DATE, D1=STATUS, E1=WORK_HOURS, F1=CONFIDENCE, G1=QUALITY, H1=FLAGS
    """
    try:
        if df.empty:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        
        with open(filename, 'w', encoding='utf-8-sig', newline='\r\n') as f:
            if include_summary:
                # Write header information
                f.write("ATTENDANCE SYSTEM REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Records: {len(df)}\n")
                if 'DATE' in df.columns:
                    f.write(f"Date Range: {df['DATE'].min()} to {df['DATE'].max()}\n")
                if 'NAME' in df.columns:
                    f.write(f"Unique Employees: {df['NAME'].nunique()}\n")
                f.write("\n")
                f.write("COLUMN STRUCTURE: A=NAME, B=TIME, C=DATE, D=STATUS, E=WORK_HOURS, F=CONFIDENCE, G=QUALITY, H=FLAGS\n")
                f.write("\n")
            
            # Create structured DataFrame
            structured_df = pd.DataFrame()
            
            # Column A: NAME
            if 'NAME' in df.columns:
                structured_df['NAME'] = df['NAME'].apply(
                    lambda x: str(x).strip().title() if pd.notna(x) else ""
                )
            else:
                structured_df['NAME'] = ""
            
            # Column B: TIME
            if 'TIME' in df.columns:
                structured_df['TIME'] = df['TIME'].apply(
                    lambda x: str(x) if pd.notna(x) else ""
                )
            else:
                structured_df['TIME'] = ""
            
            # Column C: DATE
            if 'DATE' in df.columns:
                structured_df['DATE'] = df['DATE'].apply(
                    lambda x: str(x) if pd.notna(x) else ""
                )
            else:
                structured_df['DATE'] = ""
            
            # Column D: STATUS
            if 'STATUS' in df.columns:
                structured_df['STATUS'] = df['STATUS'].apply(
                    lambda x: str(x).strip() if pd.notna(x) else ""
                )
            else:
                structured_df['STATUS'] = ""
            
            # Column E: WORK_HOURS
            if 'WORK_HOURS' in df.columns:
                structured_df['WORK_HOURS'] = df['WORK_HOURS'].apply(
                    lambda x: str(x) if pd.notna(x) and ":" in str(x) else "00:00"
                )
            else:
                structured_df['WORK_HOURS'] = "00:00"
            
            # Column F: CONFIDENCE
            if 'CONFIDENCE' in df.columns:
                structured_df['CONFIDENCE'] = df['CONFIDENCE'].apply(
                    lambda x: f"{float(x)*100:.1f}%" if pd.notna(x) and str(x).replace('.','',1).isdigit() else "N/A"
                )
            else:
                structured_df['CONFIDENCE'] = "N/A"
            
            # Column G: QUALITY
            if 'QUALITY' in df.columns:
                structured_df['QUALITY'] = df['QUALITY'].apply(
                    lambda x: f"{float(x):.3f}" if pd.notna(x) and str(x).replace('.','',1).isdigit() else "N/A"
                )
            else:
                structured_df['QUALITY'] = "N/A"
            
            # Column H: FLAGS
            if 'FLAGS' in df.columns:
                structured_df['FLAGS'] = df['FLAGS'].apply(
                    lambda x: str(x).replace("|", ", ") if pd.notna(x) and str(x) != "" else ""
                )
            else:
                structured_df['FLAGS'] = ""
            
            # Sort data
            try:
                structured_df = structured_df.sort_values(['DATE', 'NAME', 'TIME'])
            except:
                pass
            
            # Write to CSV with proper Excel formatting
            structured_df.to_csv(f, index=False, lineterminator='\n', quoting=1)
        
        print(f"✅ Excel-ready CSV created: {filename}")
        print(f"📊 Column structure: A=NAME, B=TIME, C=DATE, D=STATUS, E=WORK_HOURS, F=CONFIDENCE, G=QUALITY, H=FLAGS")
        print(f"📈 Rows: {len(structured_df)}")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error creating Excel CSV: {e}")
        return None

def create_summary_csv(df, filename_prefix="summary_export"):
    """Create summary CSV with employee statistics"""
    try:
        if df.empty or 'NAME' not in df.columns:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.csv"
        
        # Calculate employee statistics
        summary_data = []
        for name in sorted(df['NAME'].unique()):
            employee_data = df[df['NAME'] == name]
            
            stats = {
                'NAME': str(name).strip().title(),
                'TOTAL_ENTRIES': len(employee_data),
                'DAYS_ATTENDED': employee_data['DATE'].nunique() if 'DATE' in df.columns else 0,
                'CLOCK_INS': len(employee_data[employee_data['STATUS'] == 'Clock In']) if 'STATUS' in df.columns else 0,
                'CLOCK_OUTS': len(employee_data[employee_data['STATUS'] == 'Clock Out']) if 'STATUS' in df.columns else 0,
                'TOTAL_WORK_HOURS': 0
            }
            
            # Calculate total work hours
            if 'WORK_HOURS' in employee_data.columns:
                for work_hours in employee_data['WORK_HOURS']:
                    if pd.notna(work_hours) and ":" in str(work_hours):
                        try:
                            hours, minutes = str(work_hours).split(":")
                            stats['TOTAL_WORK_HOURS'] += int(hours) + int(minutes) / 60.0
                        except:
                            pass
            
            stats['TOTAL_WORK_HOURS'] = f"{stats['TOTAL_WORK_HOURS']:.1f}h"
            summary_data.append(stats)
        
        # Create DataFrame and save
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv(
            filename, 
            index=False, 
            encoding='utf-8-sig',
            lineterminator='\r\n',
            quoting=1
        )
        
        print(f"✅ Summary CSV created: {filename}")
        return filename
        
    except Exception as e:
        print(f"❌ Error creating summary CSV: {e}")
        return None

def main():
    """Test the Excel CSV formatter"""
    base_dir = Path(__file__).parent.parent
    attendance_dir = base_dir / "Attendance"
    
    if not attendance_dir.exists():
        print("❌ Attendance directory not found")
        return
    
    # Find latest attendance file
    csv_files = list(attendance_dir.glob("Attendance_*.csv"))
    if not csv_files:
        print("📄 No attendance files found")
        return
    
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"🔍 Processing: {latest_file.name}")
    
    # Read and format
    try:
        df = pd.read_csv(latest_file)
        
        # Create Excel-ready CSV
        excel_file = create_excel_ready_csv(df, "test_excel_format")
        if excel_file:
            print(f"📁 Excel file: {excel_file}")
        
        # Create summary CSV
        summary_file = create_summary_csv(df, "test_summary")
        if summary_file:
            print(f"📁 Summary file: {summary_file}")
            
    except Exception as e:
        print(f"❌ Error processing file: {e}")

if __name__ == "__main__":
    main()