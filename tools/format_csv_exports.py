#!/usr/bin/env python3
"""
CSV Export Formatter
Utility to format CSV exports with proper column structure
"""

import pandas as pd
from datetime import datetime
import os
from pathlib import Path

def format_attendance_csv(input_file, output_file=None):
    """Format attendance CSV with proper column structure"""
    try:
        # Read the CSV
        df = pd.read_csv(input_file)
        
        if df.empty:
            return None
        
        # Create formatted DataFrame with proper column names
        formatted_df = pd.DataFrame()
        
        # Column mapping and formatting
        if 'NAME' in df.columns:
            formatted_df['Name'] = df['NAME']
        
        if 'DATE' in df.columns:
            formatted_df['Date'] = df['DATE']
        
        if 'TIME' in df.columns:
            formatted_df['Time'] = df['TIME']
        
        if 'STATUS' in df.columns:
            formatted_df['Status'] = df['STATUS']
        
        if 'WORK_HOURS' in df.columns:
            formatted_df['Work Hours'] = df['WORK_HOURS'].apply(
                lambda x: str(x) if ':' in str(x) else '00:00'
            )
        
        if 'CONFIDENCE' in df.columns:
            formatted_df['Confidence'] = df['CONFIDENCE'].apply(
                lambda x: f"{float(x)*100:.1f}%" if str(x).replace('.','',1).isdigit() else str(x)
            )
        
        if 'QUALITY' in df.columns:
            formatted_df['Quality Score'] = df['QUALITY'].apply(
                lambda x: f"{float(x):.3f}" if str(x).replace('.','',1).isdigit() else str(x)
            )
        
        if 'FLAGS' in df.columns:
            formatted_df['Security Flags'] = df['FLAGS']
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = Path(input_file).stem
            output_file = f"{base_name}_formatted_{timestamp}.csv"
        
        # Save formatted CSV
        formatted_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ Formatted CSV saved: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error formatting CSV: {e}")
        return None

def main():
    """Format all attendance CSV files"""
    base_dir = Path(__file__).parent.parent
    attendance_dir = base_dir / "Attendance"
    
    if not attendance_dir.exists():
        print("❌ Attendance directory not found")
        return
    
    csv_files = list(attendance_dir.glob("Attendance_*.csv"))
    
    if not csv_files:
        print("📄 No attendance CSV files found")
        return
    
    print(f"🔍 Found {len(csv_files)} CSV files to format")
    
    formatted_dir = attendance_dir / "formatted"
    formatted_dir.mkdir(exist_ok=True)
    
    for csv_file in csv_files:
        output_file = formatted_dir / f"{csv_file.stem}_formatted.csv"
        result = format_attendance_csv(csv_file, output_file)
        
        if result:
            print(f"✅ {csv_file.name} → {output_file.name}")
        else:
            print(f"❌ Failed to format {csv_file.name}")
    
    print(f"\n📁 Formatted files saved in: {formatted_dir}")

if __name__ == "__main__":
    main()