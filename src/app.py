from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd
import os
from datetime import datetime, date, timedelta  # Import timedelta for date range
import json
from pathlib import Path
from collections import defaultdict, Counter

# Try to import numpy, fallback to built-in functions if not available
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not available, using built-in functions for calculations")

# Define paths relative to project root
BASE_DIR = Path(__file__).parent.parent  # Go up one level from src/
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
ATTENDANCE_DIR = BASE_DIR / "Attendance"
LOG_DIR = BASE_DIR / "logs"  # Added for consistency

app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))


@app.after_request
def after_request(response):
    """Clean up temporary files after each request"""
    if response.status_code == 200 and "csv" in response.content_type:
        # Schedule cleanup of temp files
        import threading

        threading.Timer(5.0, cleanup_temp_files).start()
    return response


# Create necessary directories
ATTENDANCE_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)  # Ensure log directory exists


# Helper function to cleanup temporary files
def cleanup_temp_files():
    """Clean up temporary CSV files"""
    try:
        import glob

        temp_files = (
            glob.glob("*_formatted_*.csv")
            + glob.glob("temp_*.csv")
            + glob.glob("*_patterns_*.csv")
        )
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except:
                pass
    except:
        pass


# Helper function to format CSV with proper column structure
def format_csv_for_export(df, filename_prefix="export"):
    """Format DataFrame for CSV export with proper Excel column structure (A1=NAME, B1=TIME, etc.)"""
    try:
        if df.empty:
            return None

        # Create new DataFrame with exact column order for Excel (A, B, C, D, E, F, G, H)
        formatted_df = pd.DataFrame()

        # Column A: Employee Name (A1 header)
        if "NAME" in df.columns:
            formatted_df["NAME"] = df["NAME"].apply(
                lambda x: str(x).strip().title() if pd.notna(x) else ""
            )
        else:
            formatted_df["NAME"] = ""

        # Column B: Time (B1 header)
        if "TIME" in df.columns:
            formatted_df["TIME"] = df["TIME"].apply(
                lambda x: str(x) if pd.notna(x) else ""
            )
        else:
            formatted_df["TIME"] = ""

        # Column C: Date (C1 header)
        if "DATE" in df.columns:
            formatted_df["DATE"] = df["DATE"].apply(
                lambda x: str(x) if pd.notna(x) else ""
            )
        else:
            formatted_df["DATE"] = ""

        # Column D: Status (D1 header)
        if "STATUS" in df.columns:
            formatted_df["STATUS"] = df["STATUS"].apply(
                lambda x: str(x).strip() if pd.notna(x) else ""
            )
        else:
            formatted_df["STATUS"] = ""

        # Column E: Work Hours (E1 header)
        if "WORK_HOURS" in df.columns:
            formatted_df["WORK_HOURS"] = df["WORK_HOURS"].apply(
                lambda x: str(x) if pd.notna(x) and ":" in str(x) else "00:00"
            )
        else:
            formatted_df["WORK_HOURS"] = "00:00"

        # Column F: Confidence (F1 header)
        if "CONFIDENCE" in df.columns:
            formatted_df["CONFIDENCE"] = df["CONFIDENCE"].apply(
                lambda x: (
                    f"{float(x)*100:.1f}%"
                    if pd.notna(x)
                    and str(x).replace(".", "", 1).replace("-", "", 1).isdigit()
                    else "N/A"
                )
            )
        else:
            formatted_df["CONFIDENCE"] = "N/A"

        # Column G: Quality (G1 header)
        if "QUALITY" in df.columns:
            formatted_df["QUALITY"] = df["QUALITY"].apply(
                lambda x: (
                    f"{float(x):.3f}"
                    if pd.notna(x)
                    and str(x).replace(".", "", 1).replace("-", "", 1).isdigit()
                    else "N/A"
                )
            )
        else:
            formatted_df["QUALITY"] = "N/A"

        # Column H: Flags (H1 header)
        if "FLAGS" in df.columns:
            formatted_df["FLAGS"] = df["FLAGS"].apply(
                lambda x: (
                    str(x).replace("|", ", ") if pd.notna(x) and str(x) != "" else ""
                )
            )
        else:
            formatted_df["FLAGS"] = ""

        # Sort data for better organization
        try:
            formatted_df = formatted_df.sort_values(["DATE", "NAME", "TIME"])
        except:
            pass

        # Generate filename with timestamp in base directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = str(BASE_DIR / f"{filename_prefix}_{timestamp}.csv")

        # Save with clean Excel formatting
        formatted_df.to_csv(
            filename,
            index=False,
            encoding="utf-8-sig",
            lineterminator="\r\n",
            quoting=0  # Minimal quoting for cleaner output
        )

        print(f"✅ Excel-formatted CSV created: {filename}")
        print(
            f"📊 Column structure: A=NAME, B=TIME, C=DATE, D=STATUS, E=WORK_HOURS, F=CONFIDENCE, G=QUALITY, H=FLAGS"
        )
        print(f"📈 Rows: {len(formatted_df)}")

        return filename

    except Exception as e:
        print(f"❌ Error formatting CSV: {e}")
        import traceback

        traceback.print_exc()
        return None


# Helper function to get training data information
def get_training_data_info():
    """Get information about registered faces from training data"""
    try:
        import pickle

        data_dir = BASE_DIR / "data"
        names_file = data_dir / "names.pkl"
        faces_file = data_dir / "faces_data.pkl"

        if not names_file.exists() or not faces_file.exists():
            return {"unique_faces": 0, "total_samples": 0, "names": []}

        with open(names_file, "rb") as f:
            names_data = pickle.load(f)

        unique_names = list(set(names_data))
        return {
            "unique_faces": len(unique_names),
            "total_samples": len(names_data),
            "names": sorted(unique_names),
        }
    except Exception as e:
        print(f"Error reading training data: {e}")
        return {"unique_faces": 0, "total_samples": 0, "names": []}


# Helper function to read attendance CSV with robust column handling
def read_attendance_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        # Ensure all expected columns exist, fill missing with empty string or default
        expected_cols = [
            "NAME",
            "TIME",
            "STATUS",
        ]
        for col in expected_cols:
            if col not in df.columns:
                df[col] = ""  # Add missing columns
        return df
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return pd.DataFrame(
            columns=expected_cols
        )  # Return empty DataFrame with expected columns


@app.route("/")
def index():
    """Home page with real system data"""
    today = datetime.now().strftime("%Y-%m-%d")

    # Get today's data
    today_file = ATTENDANCE_DIR / f"Attendance_{today}.csv"
    today_data = {"total_entries": 0, "unique_attendees": 0, "last_entry": None}

    if today_file.exists():
        df = read_attendance_csv(today_file)
        if not df.empty:
            today_data["total_entries"] = len(df)
            today_data["unique_attendees"] = df["NAME"].nunique()

            # Get last entry
            last_row = df.iloc[-1]
            today_data["last_entry"] = {
                "name": last_row["NAME"],
                "time": last_row["TIME"],
                "status": last_row["STATUS"],
            }

    # Get training data info
    training_info = get_training_data_info()

    return render_template(
        "index.html", today_data=today_data, training_info=training_info
    )


@app.route("/daily_attendance")
def daily_attendance():
    selected_date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    search_employee = request.args.get("employee", "").strip()
    filter_status = request.args.get("status", "")

    # Get available dates from existing files
    available_dates = []
    for file in ATTENDANCE_DIR.glob("Attendance_*.csv"):
        date_str = file.stem.replace("Attendance_", "")
        available_dates.append(date_str)
    available_dates.sort(reverse=True)

    attendance_file_path = ATTENDANCE_DIR / f"Attendance_{selected_date}.csv"

    data = {
        "date": selected_date,
        "available_dates": available_dates,
        "search_employee": search_employee,
        "filter_status": filter_status,
        "has_data": False,
        "total_entries": 0,
        "attendance_data": [],
    }

    if os.path.exists(attendance_file_path):
        df = read_attendance_csv(attendance_file_path)
        if not df.empty:
            # Apply filters
            filtered_df = df.copy()

            # Filter by employee name
            if search_employee:
                filtered_df = filtered_df[
                    filtered_df["NAME"].str.contains(
                        search_employee, case=False, na=False
                    )
                ]

            # Filter by status
            if filter_status:
                filtered_df = filtered_df[filtered_df["STATUS"] == filter_status]

            data["has_data"] = True
            data["total_entries"] = len(df)  # Total before filtering
            data["attendance_data"] = filtered_df.to_dict("records")
        else:
            print(f"File {attendance_file_path} exists but is empty or unreadable.")

    return render_template("daily_attendance.html", data=data)


@app.route("/attendance_reports")
def attendance_reports():
    """Attendance Reports - Combined Analytics and Statistics"""
    # Get filter parameters
    period_days = request.args.get("period", "30")
    custom_start = request.args.get("start_date", "")
    custom_end = request.args.get("end_date", "")

    # Calculate date range
    if period_days == "custom" and custom_start and custom_end:
        try:
            start_date = datetime.strptime(custom_start, "%Y-%m-%d").date()
            end_date = datetime.strptime(custom_end, "%Y-%m-%d").date()
            period_days = "custom"
        except ValueError:
            # Fallback to 30 days if invalid dates
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=29)
            period_days = 30
    else:
        try:
            period_days = int(period_days)
        except ValueError:
            period_days = 30
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period_days - 1)

    # Get all attendance files
    all_files = [
        f
        for f in os.listdir(ATTENDANCE_DIR)
        if f.startswith("Attendance_") and f.endswith(".csv")
    ]

    # Filter files by date range
    filtered_files = []
    for file_name in all_files:
        try:
            date_str = file_name.replace("Attendance_", "").replace(".csv", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if start_date <= file_date <= end_date:
                filtered_files.append(file_name)
        except ValueError:
            continue

    reports_data = {
        "has_data": False,
        "period_days": period_days,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "custom_start": custom_start,
        "custom_end": custom_end,
        "total_users": 0,
        "total_entries": 0,
        "employee_attendance": [],
        "charts_enabled": True,
        "daily_stats": {},
        "summary_stats": {},
    }

    if filtered_files:
        try:
            all_data_frames = []
            daily_stats = {}

            for file_name in filtered_files:
                df = read_attendance_csv(ATTENDANCE_DIR / file_name)
                if not df.empty:
                    all_data_frames.append(df)

                    date_str = file_name.replace("Attendance_", "").replace(".csv", "")
                    daily_stats[date_str] = {
                        "total_entries": len(df),
                        "unique_users": df["NAME"].nunique(),
                        "clock_ins": len(df[df["STATUS"] == "Clock In"]),
                        "clock_outs": len(df[df["STATUS"] == "Clock Out"]),
                    }

            if all_data_frames:
                combined_df = pd.concat(all_data_frames, ignore_index=True)
                reports_data["has_data"] = True
                reports_data["total_users"] = combined_df["NAME"].nunique()
                reports_data["total_entries"] = len(combined_df)

                # Employee Attendance Patterns
                employee_stats = (
                    combined_df.groupby("NAME")
                    .agg({"TIME": "count", "STATUS": lambda x: (x == "Clock In").sum()})
                    .reset_index()
                )
                employee_stats.columns = [
                    "Employee Name",
                    "Total Entries",
                    "Clock In Count",
                ]

                # Calculate attendance rate
                total_possible_days = len(filtered_files)
                if total_possible_days > 0:
                    employee_stats["Attendance Rate (%)"] = (
                        employee_stats["Clock In Count"] / total_possible_days * 100
                    ).round(1)
                else:
                    employee_stats["Attendance Rate (%)"] = 0.0

                reports_data["employee_attendance"] = employee_stats.sort_values(
                    "Total Entries", ascending=False
                ).to_dict("records")

                reports_data["daily_stats"] = daily_stats

                # Get all registered users from training data
                all_registered_users = set()
                try:
                    import pickle
                    from pathlib import Path

                    BASE_DIR = Path(__file__).parent.parent
                    names_file = BASE_DIR / "data" / "names.pkl"
                    if names_file.exists():
                        with open(names_file, "rb") as f:
                            names_data = pickle.load(f)
                            all_registered_users = set(names_data)
                except Exception as e:
                    print(f"Error loading registered users: {e}")
                    all_registered_users = set(combined_df["NAME"].unique())

                # Calculate absence tracking
                today = datetime.now().strftime("%Y-%m-%d")
                today_file = ATTENDANCE_DIR / f"Attendance_{today}.csv"

                absent_today = []
                present_today = set()

                if today_file.exists():
                    today_df = read_attendance_csv(today_file)
                    if not today_df.empty:
                        present_today = set(today_df["NAME"].unique())

                absent_today = list(all_registered_users - present_today)

                # Absence statistics for the period
                period_attendance = {}
                for user in all_registered_users:
                    user_data = combined_df[combined_df["NAME"] == user]
                    days_present = len(user_data[user_data["STATUS"] == "Clock In"])
                    total_days = len(filtered_files)
                    absence_rate = (
                        (total_days - days_present) / max(total_days, 1)
                    ) * 100

                    period_attendance[user] = {
                        "days_present": days_present,
                        "days_absent": total_days - days_present,
                        "absence_rate": round(absence_rate, 1),
                    }

                # Summary statistics
                reports_data["summary_stats"] = {
                    "total_clock_ins": len(
                        combined_df[combined_df["STATUS"] == "Clock In"]
                    ),
                    "total_clock_outs": len(
                        combined_df[combined_df["STATUS"] == "Clock Out"]
                    ),
                    "avg_entries_per_day": round(
                        len(combined_df) / max(len(filtered_files), 1), 1
                    ),
                    "most_active_day": (
                        max(daily_stats.items(), key=lambda x: x[1]["total_entries"])[0]
                        if daily_stats
                        else "N/A"
                    ),
                }

                # Working Hours Analysis - Simplified
                working_hours_analysis = {}
                daily_working_hours = {}

                # Group data by date and user
                for date_str in filtered_files:
                    date_only = date_str.replace("Attendance_", "").replace(".csv", "")
                    date_file = ATTENDANCE_DIR / date_str

                    if date_file.exists():
                        try:
                            day_df = read_attendance_csv(date_file)
                            if not day_df.empty:
                                # Process each user for this date
                                for user in day_df["NAME"].unique():
                                    user_day_data = day_df[day_df["NAME"] == user]

                                    clock_ins = user_day_data[
                                        user_day_data["STATUS"] == "Clock In"
                                    ]
                                    clock_outs = user_day_data[
                                        user_day_data["STATUS"] == "Clock Out"
                                    ]

                                    if not clock_ins.empty and not clock_outs.empty:
                                        try:
                                            # Get first clock in and last clock out
                                            first_in_time = clock_ins.iloc[0]["TIME"]
                                            last_out_time = clock_outs.iloc[-1]["TIME"]

                                            # Parse time (handle both HH:MM and HH:MM:SS)
                                            if len(first_in_time.split(":")) == 3:
                                                first_in = datetime.strptime(
                                                    first_in_time, "%H:%M:%S"
                                                )
                                                last_out = datetime.strptime(
                                                    last_out_time, "%H:%M:%S"
                                                )
                                            else:
                                                first_in = datetime.strptime(
                                                    first_in_time, "%H:%M"
                                                )
                                                last_out = datetime.strptime(
                                                    last_out_time, "%H:%M"
                                                )

                                            # Calculate hours worked
                                            hours_worked = (
                                                last_out - first_in
                                            ).total_seconds() / 3600

                                            if (
                                                hours_worked > 0 and hours_worked <= 16
                                            ):  # Reasonable work day
                                                if user not in working_hours_analysis:
                                                    working_hours_analysis[user] = {
                                                        "total_hours": 0,
                                                        "working_days": 0,
                                                        "daily_hours": [],
                                                    }

                                                working_hours_analysis[user][
                                                    "total_hours"
                                                ] += hours_worked
                                                working_hours_analysis[user][
                                                    "working_days"
                                                ] += 1
                                                working_hours_analysis[user][
                                                    "daily_hours"
                                                ].append(hours_worked)

                                                if date_only not in daily_working_hours:
                                                    daily_working_hours[date_only] = []
                                                daily_working_hours[date_only].append(
                                                    {
                                                        "user": user,
                                                        "hours": round(hours_worked, 1),
                                                        "clock_in": first_in_time,
                                                        "clock_out": last_out_time,
                                                    }
                                                )
                                        except (ValueError, IndexError) as e:
                                            print(
                                                f"Error processing time for {user} on {date_only}: {e}"
                                            )
                                            continue
                        except Exception as e:
                            print(f"Error reading file {date_str}: {e}")
                            continue

                # Calculate final statistics
                for user, data in working_hours_analysis.items():
                    daily_hours = data["daily_hours"]
                    working_days = data["working_days"]
                    total_hours = data["total_hours"]

                    avg_hours = total_hours / max(working_days, 1)
                    max_hours = max(daily_hours) if daily_hours else 0
                    min_hours = min(daily_hours) if daily_hours else 0

                    working_hours_analysis[user] = {
                        "total_hours": round(total_hours, 1),
                        "working_days": working_days,
                        "avg_hours_per_day": round(avg_hours, 1),
                        "max_hours": round(max_hours, 1),
                        "min_hours": round(min_hours, 1),
                        "efficiency": (
                            round((avg_hours / 8) * 100, 1) if avg_hours > 0 else 0
                        ),
                    }

                # Calculate overall working hours stats
                all_daily_hours = []
                for date_hours in daily_working_hours.values():
                    for entry in date_hours:
                        all_daily_hours.append(entry["hours"])

                working_hours_summary = {
                    "total_working_hours": sum(all_daily_hours),
                    "avg_daily_hours": round(
                        sum(all_daily_hours) / max(len(all_daily_hours), 1), 1
                    ),
                    "max_daily_hours": (
                        round(max(all_daily_hours), 1) if all_daily_hours else 0
                    ),
                    "min_daily_hours": (
                        round(min(all_daily_hours), 1) if all_daily_hours else 0
                    ),
                    "standard_hours": 8,  # Standard working hours
                    "overtime_threshold": 9,  # Hours considered overtime
                }

                # Absence tracking data
                reports_data["absence_tracking"] = {
                    "absent_today": sorted(absent_today),
                    "present_today": sorted(list(present_today)),
                    "total_registered": len(all_registered_users),
                    "period_attendance": period_attendance,
                    "today_date": today,
                }

                # Working hours data
                reports_data["working_hours"] = {
                    "analysis": working_hours_analysis,
                    "daily_hours": daily_working_hours,
                    "summary": working_hours_summary,
                }

        except Exception as e:
            print(f"Error generating attendance reports: {e}")

    return render_template("attendance_reports.html", data=reports_data)


@app.route("/download_csv")
def download_csv():
    date_str = request.args.get("date")
    if date_str:
        file_path = ATTENDANCE_DIR / f"Attendance_{date_str}.csv"
        if os.path.exists(file_path):
            try:
                # Read and format the CSV
                df = read_attendance_csv(file_path)
                if not df.empty:
                    formatted_file = format_csv_for_export(df, f"attendance_{date_str}")
                    if formatted_file:
                        return send_file(
                            formatted_file,
                            as_attachment=True,
                            download_name=f"attendance_{date_str}_formatted.csv",
                            mimetype="text/csv",
                        )

                # Fallback to original file if formatting fails
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=f"attendance_{date_str}.csv",
                    mimetype="text/csv",
                )
            except Exception as e:
                print(f"Error formatting CSV for download: {e}")
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=f"attendance_{date_str}.csv",
                    mimetype="text/csv",
                )
    return "File not found", 404


@app.route("/download_patterns")
def download_patterns():
    attendance_files = [
        f
        for f in os.listdir(ATTENDANCE_DIR)
        if f.startswith("Attendance_") and f.endswith(".csv")
    ]

    if attendance_files:
        try:
            all_data_frames = []
            for file_name in attendance_files:
                df = read_attendance_csv(ATTENDANCE_DIR / file_name)
                if not df.empty:
                    all_data_frames.append(df)

            if all_data_frames:
                combined_df = pd.concat(all_data_frames, ignore_index=True)
                total_attendance_days = combined_df["DATE"].nunique()

                # Calculate comprehensive patterns
                days_attended = (
                    combined_df.groupby("NAME")["DATE"]
                    .nunique()
                    .reset_index(name="Days Attended")
                )
                total_entries_per_person = (
                    combined_df.groupby("NAME").size().reset_index(name="Total Entries")
                )

                # Add work hours calculation
                work_hours_per_person = (
                    combined_df.groupby("NAME")["WORK_HOURS"]
                    .apply(
                        lambda x: sum(
                            [
                                int(wh.split(":")[0]) + int(wh.split(":")[1]) / 60.0
                                for wh in x
                                if ":" in str(wh) and str(wh) != "00:00"
                            ]
                        )
                    )
                    .reset_index(name="Total Work Hours")
                )

                # Merge all data
                attendance_patterns = days_attended.merge(
                    total_entries_per_person, on="NAME", how="left"
                ).merge(work_hours_per_person, on="NAME", how="left")

                # Calculate additional metrics
                if total_attendance_days > 0:
                    attendance_patterns["Attendance Rate (%)"] = (
                        attendance_patterns["Days Attended"]
                        / total_attendance_days
                        * 100
                    ).round(2)
                else:
                    attendance_patterns["Attendance Rate (%)"] = 0.0

                attendance_patterns["Average Hours/Day"] = (
                    attendance_patterns["Total Work Hours"]
                    / attendance_patterns["Days Attended"].replace(0, 1)
                ).round(2)

                # Clean up data
                attendance_patterns = attendance_patterns.fillna(0)
                attendance_patterns["Total Entries"] = attendance_patterns[
                    "Total Entries"
                ].astype(int)
                attendance_patterns["Total Work Hours"] = attendance_patterns[
                    "Total Work Hours"
                ].round(2)

                # Create Excel-ready DataFrame with proper column structure
                excel_df = pd.DataFrame()
                excel_df["NAME"] = attendance_patterns["NAME"].apply(
                    lambda x: str(x).strip().title()
                )
                excel_df["DAYS_ATTENDED"] = attendance_patterns["Days Attended"]
                excel_df["TOTAL_ENTRIES"] = attendance_patterns["Total Entries"]
                excel_df["TOTAL_WORK_HOURS"] = attendance_patterns[
                    "Total Work Hours"
                ].apply(lambda x: f"{x:.1f}h")
                excel_df["ATTENDANCE_RATE"] = attendance_patterns[
                    "Attendance Rate (%)"
                ].apply(lambda x: f"{x:.1f}%")
                excel_df["AVG_HOURS_DAY"] = attendance_patterns[
                    "Average Hours/Day"
                ].apply(lambda x: f"{x:.1f}h")

                # Generate formatted CSV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_file = f"attendance_patterns_{timestamp}.csv"

                # Save with proper Excel formatting
                excel_df.to_csv(
                    temp_file,
                    index=False,
                    encoding="utf-8-sig",
                    lineterminator="\r\n",
                    quoting=1,
                )

                return send_file(
                    temp_file,
                    as_attachment=True,
                    download_name=f"attendance_patterns_{timestamp}.csv",
                    mimetype="text/csv",
                )

        except Exception as e:
            print(f"Error generating patterns for download: {e}")
            import traceback

            traceback.print_exc()
    return "No data available", 404


@app.route("/api/attendance_status")
def get_attendance_status():
    """API endpoint to get current attendance status for real-time updates"""
    today = datetime.now().strftime("%Y-%m-%d")
    attendance_file_path = ATTENDANCE_DIR / f"Attendance_{today}.csv"

    status = {
        "date": today,
        "total_entries": 0,
        "present_count": 0,  # Keep present_count for compatibility
        "unique_attendees": 0,
        "last_entry": None,
    }

    if os.path.exists(attendance_file_path):
        df = read_attendance_csv(attendance_file_path)
        if not df.empty:
            status["total_entries"] = len(df)
            status["unique_attendees"] = df["NAME"].nunique()
            status["present_count"] = df["NAME"].nunique()  # Same as unique attendees

            last_row = df.iloc[-1]
            status["last_entry"] = {
                "name": last_row["NAME"],
                "time": last_row["TIME"],
                "status": last_row["STATUS"],
            }
        else:
            print(
                f"File {attendance_file_path} exists but is empty or unreadable for API."
            )
    return jsonify(status)


@app.route("/dashboard")
def dashboard():
    """Enhanced Dashboard with real-time charts and analytics"""
    today = datetime.now().strftime("%Y-%m-%d")

    dashboard_data = {
        "today_summary": None,
        "recent_activity": [],
        "system_status": {
            "components": {
                "attendance_system": {"enabled": True, "status": "active"},
                "data_storage": {"enabled": True, "status": "active"},
                "web_interface": {"enabled": True, "status": "active"},
            },
            "metrics": {
                "total_users": 0,
                "total_records": 0,
                "system_uptime": "Running",
                "last_backup": "None",
            },
        },
        "charts_enabled": True,  # Enable charts
        "realtime_updates": True,  # Enable real-time updates
    }

    try:
        # Get today's summary
        today_file = ATTENDANCE_DIR / f"Attendance_{today}.csv"
        if today_file.exists():
            df_today = read_attendance_csv(today_file)

            if not df_today.empty:
                unique_people_today = df_today["NAME"].nunique()
                total_entries_today = len(df_today)
                clock_ins_today = len(df_today[df_today["STATUS"] == "Clock In"])
                clock_outs_today = len(df_today[df_today["STATUS"] == "Clock Out"])

                # Work hours calculation removed - not available in new format
                avg_work_hours_today = 0

                # Top attendees based on total entries today
                top_attendees_counts = df_today["NAME"].value_counts().head(5)
                top_attendees_list = [
                    {"name": name, "count": count}
                    for name, count in top_attendees_counts.items()
                ]

                # Quality metrics removed - not available in new format

                dashboard_data["today_summary"] = {
                    "total_unique_attendees": unique_people_today,
                    "total_entries": total_entries_today,
                    "clock_ins": clock_ins_today,
                    "clock_outs": clock_outs_today,
                    "attendance_rate": round(
                        (unique_people_today / max(df_today["NAME"].nunique(), 1))
                        * 100,
                        1,
                    ),
                    "top_attendees": top_attendees_list,
                }

                # Get recent activity (last 15 entries)
                recent_entries = df_today.tail(15).to_dict("records")
                dashboard_data["recent_activity"] = recent_entries

        # Calculate system metrics (total users, total records across all time)
        all_files = list(ATTENDANCE_DIR.glob("Attendance_*.csv"))
        total_records_all_time = 0
        unique_users_all_time = set()

        for file in all_files:
            try:
                df = read_attendance_csv(file)
                total_records_all_time += len(df)
                unique_users_all_time.update(df["NAME"].unique())
            except Exception as e:
                print(f"Error processing {file} for dashboard metrics: {e}")
                continue

        dashboard_data["system_status"]["metrics"]["total_users"] = len(
            unique_users_all_time
        )
        dashboard_data["system_status"]["metrics"][
            "total_records"
        ] = total_records_all_time

        # Add system health indicators
        dashboard_data["system_status"]["health"] = {
            "data_files_accessible": len(all_files),
            "log_directory_status": "accessible" if LOG_DIR.exists() else "error",
            "attendance_directory_status": (
                "accessible" if ATTENDANCE_DIR.exists() else "error"
            ),
            "latest_activity": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    except Exception as e:
        print(f"Error generating dashboard data: {e}")
        import traceback

        traceback.print_exc()

    return render_template("dashboard.html", data=dashboard_data)


@app.route("/settings")
def settings():
    """Settings page"""
    return render_template("settings.html")


@app.route("/api/settings/current")
def get_current_settings():
    """Get current system settings"""
    settings = {
        "system_name": "Smart Attendance System",
        "timezone": "Asia/Jakarta",
        "backup_enabled": True,
        "auto_backup_days": 7,
        "items_per_page": 25,
        "show_timestamps": True,
        "enable_logging": True,  # Default to True for security
        "session_timeout": 60,
        "min_face_quality_setting": 0.75,  # Exposed setting from take_attendance
        "confidence_threshold_setting": 0.6,  # Exposed setting from take_attendance
        "max_daily_records_setting": 10,  # Exposed setting from take_attendance
        "suspicious_interval_setting": 30,  # Exposed setting from take_attendance
    }

    config_file = BASE_DIR / "config" / "settings.json"
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                saved_settings = json.load(f)
                settings.update(saved_settings)
        except Exception as e:
            print(f"Error loading settings from file: {e}")

    return jsonify(settings)


@app.route("/api/settings/save", methods=["POST"])
def save_settings():
    """Save system settings"""
    try:
        settings = request.get_json()
        if not isinstance(settings, dict):
            return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

        config_dir = BASE_DIR / "config"
        config_dir.mkdir(exist_ok=True)

        config_file = config_dir / "settings.json"
        with open(config_file, "w") as f:
            json.dump(settings, f, indent=2)

        return jsonify({"success": True, "message": "Settings saved successfully"})
    except Exception as e:
        print(f"Error saving settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/system/status")
def get_system_status():
    """API to get real-time system status"""
    status = {
        "components": {
            "attendance_system": {
                "enabled": True,
                "status": "active",
            },  # This would ideally reflect if the `take_attendance` script is running
            "data_storage": {
                "enabled": True,
                "status": "active",
                "path": str(ATTENDANCE_DIR),
            },
            "web_interface": {"enabled": True, "status": "active"},
        },
        "timestamp": datetime.now().isoformat(),
        "last_log_entry": "N/A",
        "disk_space_free_gb": "N/A",  # Needs system call to check disk space
    }

    # Check last log entry (for basic health check)
    current_month_log_file = (
        LOG_DIR / f"suspicious_activities_{datetime.now().strftime('%Y-%m')}.log"
    )
    if current_month_log_file.exists():
        try:
            with open(current_month_log_file, "r") as f:
                lines = f.readlines()
                if lines:
                    status["last_log_entry"] = lines[-1].strip()
        except Exception as e:
            status["last_log_entry"] = f"Error reading log: {e}"

    # Basic disk space check (might need `shutil` or `os.statvfs` for more robust check)
    try:
        stat = os.statvfs("/")
        free_bytes = stat.f_bfree * stat.f_bsize
        status["disk_space_free_gb"] = round(free_bytes / (1024**3), 2)
    except Exception as e:
        status["disk_space_free_gb"] = f"Error: {e}"

    return jsonify(status)


# Security features removed


# ========================= NEW API ENDPOINTS FOR CHARTS AND STATISTICS =========================


@app.route("/api/charts/daily_attendance")
def api_daily_attendance_chart():
    """API endpoint for daily attendance chart data"""
    days = int(request.args.get("days", 7))  # Default last 7 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    chart_data = {
        "labels": [],
        "datasets": {
            "clock_in": [],
            "clock_out": [],
            "unique_attendees": [],
            "total_entries": [],
        },
    }

    try:
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            chart_data["labels"].append(current_date.strftime("%m/%d"))

            attendance_file = ATTENDANCE_DIR / f"Attendance_{date_str}.csv"

            if attendance_file.exists():
                df = read_attendance_csv(attendance_file)
                if not df.empty:
                    clock_in_count = len(df[df["STATUS"] == "Clock In"])
                    clock_out_count = len(df[df["STATUS"] == "Clock Out"])
                    unique_count = df["NAME"].nunique()
                    total_count = len(df)

                    chart_data["datasets"]["clock_in"].append(clock_in_count)
                    chart_data["datasets"]["clock_out"].append(clock_out_count)
                    chart_data["datasets"]["unique_attendees"].append(unique_count)
                    chart_data["datasets"]["total_entries"].append(total_count)
                else:
                    chart_data["datasets"]["clock_in"].append(0)
                    chart_data["datasets"]["clock_out"].append(0)
                    chart_data["datasets"]["unique_attendees"].append(0)
                    chart_data["datasets"]["total_entries"].append(0)
            else:
                chart_data["datasets"]["clock_in"].append(0)
                chart_data["datasets"]["clock_out"].append(0)
                chart_data["datasets"]["unique_attendees"].append(0)
                chart_data["datasets"]["total_entries"].append(0)

            current_date += timedelta(days=1)

    except Exception as e:
        print(f"Error generating daily attendance chart: {e}")

    return jsonify(chart_data)


@app.route("/api/charts/hourly_patterns")
def api_hourly_patterns_chart():
    """API endpoint for hourly attendance patterns"""
    days_back = int(request.args.get("days", 30))  # Default last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back - 1)

    hourly_data = defaultdict(lambda: {"clock_in": 0, "clock_out": 0})

    try:
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            attendance_file = ATTENDANCE_DIR / f"Attendance_{date_str}.csv"

            if attendance_file.exists():
                df = read_attendance_csv(attendance_file)
                if not df.empty:
                    for _, row in df.iterrows():
                        try:
                            time_obj = datetime.strptime(row["TIME"], "%H:%M:%S").time()
                            hour = time_obj.hour
                            if row["STATUS"] == "Clock In":
                                hourly_data[hour]["clock_in"] += 1
                            elif row["STATUS"] == "Clock Out":
                                hourly_data[hour]["clock_out"] += 1
                        except ValueError:
                            continue

            current_date += timedelta(days=1)

        # Convert to chart format
        chart_data = {
            "labels": [f"{hour:02d}:00" for hour in range(24)],
            "datasets": {
                "clock_in": [hourly_data[hour]["clock_in"] for hour in range(24)],
                "clock_out": [hourly_data[hour]["clock_out"] for hour in range(24)],
            },
        }

    except Exception as e:
        print(f"Error generating hourly patterns chart: {e}")
        chart_data = {"labels": [], "datasets": {"clock_in": [], "clock_out": []}}

    return jsonify(chart_data)


@app.route("/api/charts/user_attendance")
def api_user_attendance_chart():
    """API endpoint for individual user attendance statistics"""
    days_back = int(request.args.get("days", 30))
    limit = int(request.args.get("limit", 10))  # Top N users
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back - 1)

    user_stats = defaultdict(
        lambda: {"days_attended": set(), "total_entries": 0, "total_hours": 0.0}
    )

    try:
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            attendance_file = ATTENDANCE_DIR / f"Attendance_{date_str}.csv"

            if attendance_file.exists():
                df = read_attendance_csv(attendance_file)
                if not df.empty:
                    for name in df["NAME"].unique():
                        user_data = df[df["NAME"] == name]
                        user_stats[name]["days_attended"].add(date_str)
                        user_stats[name]["total_entries"] += len(user_data)

                        # Calculate work hours for this day
                        work_hours = (
                            user_data["WORK_HOURS"].iloc[-1]
                            if len(user_data) > 0
                            else "00:00"
                        )
                        try:
                            if ":" in str(work_hours):
                                h, m = map(int, str(work_hours).split(":"))
                                user_stats[name]["total_hours"] += h + m / 60.0
                        except (ValueError, AttributeError):
                            pass

            current_date += timedelta(days=1)

        # Convert to chart format
        sorted_users = sorted(
            user_stats.items(), key=lambda x: len(x[1]["days_attended"]), reverse=True
        )[:limit]

        chart_data = {
            "labels": [user[0] for user in sorted_users],
            "datasets": {
                "days_attended": [
                    len(user[1]["days_attended"]) for user in sorted_users
                ],
                "total_entries": [user[1]["total_entries"] for user in sorted_users],
                "avg_hours_per_day": [
                    round(
                        user[1]["total_hours"] / max(len(user[1]["days_attended"]), 1),
                        2,
                    )
                    for user in sorted_users
                ],
            },
        }

    except Exception as e:
        print(f"Error generating user attendance chart: {e}")
        chart_data = {
            "labels": [],
            "datasets": {
                "days_attended": [],
                "total_entries": [],
                "avg_hours_per_day": [],
            },
        }

    return jsonify(chart_data)


@app.route("/api/charts/quality_metrics")
def api_quality_metrics_chart():
    """API endpoint for face recognition quality and confidence metrics"""
    days_back = int(request.args.get("days", 7))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back - 1)

    daily_metrics = defaultdict(lambda: {"quality_scores": [], "confidence_scores": []})

    try:
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            attendance_file = ATTENDANCE_DIR / f"Attendance_{date_str}.csv"

            if attendance_file.exists():
                df = read_attendance_csv(attendance_file)
                if not df.empty:
                    # Extract quality scores
                    quality_scores = []
                    confidence_scores = []

                    for _, row in df.iterrows():
                        try:
                            if str(row["QUALITY"]).replace(".", "", 1).isdigit():
                                quality_scores.append(float(row["QUALITY"]))
                        except (ValueError, TypeError):
                            pass

                        try:
                            if str(row["CONFIDENCE"]).replace(".", "", 1).isdigit():
                                confidence_scores.append(float(row["CONFIDENCE"]))
                        except (ValueError, TypeError):
                            pass

                    daily_metrics[date_str]["quality_scores"] = quality_scores
                    daily_metrics[date_str]["confidence_scores"] = confidence_scores

            current_date += timedelta(days=1)

        # Calculate daily averages
        chart_data = {
            "labels": [],
            "datasets": {
                "avg_quality": [],
                "avg_confidence": [],
                "low_quality_count": [],
                "low_confidence_count": [],
            },
        }

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            chart_data["labels"].append(current_date.strftime("%m/%d"))

            quality_scores = daily_metrics[date_str]["quality_scores"]
            confidence_scores = daily_metrics[date_str]["confidence_scores"]

            avg_quality = np.mean(quality_scores) if quality_scores else 0
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
            low_quality = len([q for q in quality_scores if q < 0.6])
            low_confidence = len([c for c in confidence_scores if c < 0.7])

            chart_data["datasets"]["avg_quality"].append(round(avg_quality, 3))
            chart_data["datasets"]["avg_confidence"].append(round(avg_confidence, 3))
            chart_data["datasets"]["low_quality_count"].append(low_quality)
            chart_data["datasets"]["low_confidence_count"].append(low_confidence)

            current_date += timedelta(days=1)

    except Exception as e:
        print(f"Error generating quality metrics chart: {e}")
        chart_data = {
            "labels": [],
            "datasets": {
                "avg_quality": [],
                "avg_confidence": [],
                "low_quality_count": [],
                "low_confidence_count": [],
            },
        }

    return jsonify(chart_data)


@app.route("/api/realtime/current_status")
def api_realtime_status():
    """Real-time system status API"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")

        # Today's data
        today_file = ATTENDANCE_DIR / f"Attendance_{today}.csv"
        today_stats = {
            "total_entries": 0,
            "unique_attendees": 0,
            "clock_ins": 0,
            "clock_outs": 0,
            "last_entry": None,
        }

        if today_file.exists():
            df = read_attendance_csv(today_file)
            if not df.empty:
                today_stats["total_entries"] = len(df)
                today_stats["unique_attendees"] = df["NAME"].nunique()
                today_stats["clock_ins"] = len(df[df["STATUS"] == "Clock In"])
                today_stats["clock_outs"] = len(df[df["STATUS"] == "Clock Out"])

                # Last entry
                last_row = df.iloc[-1]
                today_stats["last_entry"] = {
                    "name": last_row["NAME"],
                    "time": last_row["TIME"],
                    "status": last_row["STATUS"],
                    "confidence": last_row.get("CONFIDENCE", "N/A"),
                    "quality": last_row.get("QUALITY", "N/A"),
                }

        # System metrics
        all_files = list(ATTENDANCE_DIR.glob("Attendance_*.csv"))
        total_users_all_time = set()
        total_records_all_time = 0

        for file in all_files:
            try:
                df = read_attendance_csv(file)
                total_records_all_time += len(df)
                total_users_all_time.update(df["NAME"].unique())
            except Exception:
                continue

        # Recent activity (last 10 entries from today)
        recent_activity = []
        if today_file.exists():
            df = read_attendance_csv(today_file)
            if not df.empty:
                recent_df = df.tail(10)
                recent_activity = recent_df.to_dict("records")

        # Get training data information
        training_data_info = get_training_data_info()

        status_data = {
            "timestamp": datetime.now().isoformat(),
            "current_date": today,
            "current_time": current_time,
            "today": today_stats,
            "system_totals": {
                "total_registered_users": len(total_users_all_time),
                "total_records_all_time": total_records_all_time,
                "active_days": len(all_files),
            },
            "recent_activity": recent_activity,
            "training_data": training_data_info,
            "system_health": {
                "attendance_files_accessible": len(all_files),
                "log_directory_accessible": LOG_DIR.exists(),
                "data_directory_accessible": ATTENDANCE_DIR.exists(),
            },
        }

        return jsonify(status_data)

    except Exception as e:
        print(f"Error getting realtime status: {e}")
        return jsonify({"error": str(e), "timestamp": datetime.now().isoformat()}), 500


@app.route("/api/analytics/summary")
def api_analytics_summary():
    """Comprehensive analytics summary API"""
    days_back = int(request.args.get("days", 30))
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back - 1)

    try:
        # Collect all data for the period
        all_data = []
        attendance_days = 0

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            attendance_file = ATTENDANCE_DIR / f"Attendance_{date_str}.csv"

            if attendance_file.exists():
                df = read_attendance_csv(attendance_file)
                if not df.empty:
                    df["DATE_PARSED"] = current_date
                    all_data.append(df)
                    attendance_days += 1

            current_date += timedelta(days=1)

        if not all_data:
            return jsonify(
                {
                    "period": {
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "total_days": days_back,
                        "active_days": 0,
                    },
                    "attendance_summary": {
                        "total_entries": 0,
                        "unique_users": 0,
                        "total_clock_ins": 0,
                        "total_clock_outs": 0,
                        "avg_entries_per_day": 0,
                    },
                    "quality_analytics": {
                        "avg_quality_score": 0,
                        "avg_confidence_score": 0,
                    },
                    "message": "No data found for the specified period",
                }
            )

        combined_df = pd.concat(all_data, ignore_index=True)

        # Calculate comprehensive analytics
        analytics = {
            "period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "total_days": days_back,
                "active_days": attendance_days,
            },
            "attendance_summary": {
                "total_entries": len(combined_df),
                "unique_users": combined_df["NAME"].nunique(),
                "total_clock_ins": len(
                    combined_df[combined_df["STATUS"] == "Clock In"]
                ),
                "total_clock_outs": len(
                    combined_df[combined_df["STATUS"] == "Clock Out"]
                ),
                "avg_entries_per_day": round(
                    len(combined_df) / max(attendance_days, 1), 2
                ),
                "avg_users_per_day": round(
                    combined_df.groupby("DATE")["NAME"].nunique().mean(), 2
                ),
            },
            "user_analytics": {
                "most_active_user": None,
                "least_active_user": None,
                "attendance_rates": [],
            },
            "time_patterns": {
                "peak_clock_in_hour": None,
                "peak_clock_out_hour": None,
                "busiest_day_of_week": None,
            },
            "quality_analytics": {
                "avg_quality_score": 0,
                "avg_confidence_score": 0,
                "low_quality_percentage": 0,
                "low_confidence_percentage": 0,
            },
        }

        # User analytics
        user_counts = combined_df["NAME"].value_counts()
        if len(user_counts) > 0:
            analytics["user_analytics"]["most_active_user"] = {
                "name": user_counts.index[0],
                "entries": int(user_counts.iloc[0]),
            }
            analytics["user_analytics"]["least_active_user"] = {
                "name": user_counts.index[-1],
                "entries": int(user_counts.iloc[-1]),
            }

        # Time pattern analytics
        try:
            clock_in_hours = []
            clock_out_hours = []

            for _, row in combined_df.iterrows():
                try:
                    time_obj = datetime.strptime(row["TIME"], "%H:%M:%S").time()
                    if row["STATUS"] == "Clock In":
                        clock_in_hours.append(time_obj.hour)
                    elif row["STATUS"] == "Clock Out":
                        clock_out_hours.append(time_obj.hour)
                except ValueError:
                    continue

            if clock_in_hours:
                analytics["time_patterns"]["peak_clock_in_hour"] = Counter(
                    clock_in_hours
                ).most_common(1)[0][0]
            if clock_out_hours:
                analytics["time_patterns"]["peak_clock_out_hour"] = Counter(
                    clock_out_hours
                ).most_common(1)[0][0]

        except Exception as e:
            print(f"Error analyzing time patterns: {e}")

        # Quality analytics
        try:
            quality_scores = []
            confidence_scores = []

            for _, row in combined_df.iterrows():
                try:
                    if str(row["QUALITY"]).replace(".", "", 1).isdigit():
                        quality_scores.append(float(row["QUALITY"]))
                except (ValueError, TypeError):
                    pass

                try:
                    if str(row["CONFIDENCE"]).replace(".", "", 1).isdigit():
                        confidence_scores.append(float(row["CONFIDENCE"]))
                except (ValueError, TypeError):
                    pass

            if quality_scores:
                analytics["quality_analytics"]["avg_quality_score"] = round(
                    np.mean(quality_scores), 3
                )
                analytics["quality_analytics"]["low_quality_percentage"] = round(
                    len([q for q in quality_scores if q < 0.6])
                    / len(quality_scores)
                    * 100,
                    2,
                )

            if confidence_scores:
                analytics["quality_analytics"]["avg_confidence_score"] = round(
                    np.mean(confidence_scores), 3
                )
                analytics["quality_analytics"]["low_confidence_percentage"] = round(
                    len([c for c in confidence_scores if c < 0.7])
                    / len(confidence_scores)
                    * 100,
                    2,
                )

        except Exception as e:
            print(f"Error analyzing quality metrics: {e}")

        return jsonify(analytics)

    except Exception as e:
        print(f"Error generating analytics summary: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/download_comprehensive")
def download_comprehensive():
    """Download comprehensive attendance report"""
    date_str = request.args.get("date")
    report_type = request.args.get("type", "daily")

    try:
        if report_type == "daily" and date_str:
            file_path = ATTENDANCE_DIR / f"Attendance_{date_str}.csv"
            if file_path.exists():
                df = read_attendance_csv(file_path)
                if not df.empty:
                    formatted_file = format_csv_for_export(
                        df, f"comprehensive_daily_{date_str}"
                    )
                    if formatted_file:
                        return send_file(
                            formatted_file,
                            as_attachment=True,
                            download_name=f"comprehensive_daily_{date_str}.csv",
                            mimetype="text/csv",
                        )

        elif report_type == "weekly":
            if date_str:
                start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                start_date = datetime.now().date() - timedelta(days=6)

            all_data = []
            for i in range(7):
                current_date = start_date + timedelta(days=i)
                file_path = (
                    ATTENDANCE_DIR
                    / f"Attendance_{current_date.strftime('%Y-%m-%d')}.csv"
                )
                if file_path.exists():
                    df = read_attendance_csv(file_path)
                    if not df.empty:
                        all_data.append(df)

            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                formatted_file = format_csv_for_export(
                    combined_df, f"comprehensive_weekly_{start_date}"
                )
                if formatted_file:
                    return send_file(
                        formatted_file,
                        as_attachment=True,
                        download_name=f"comprehensive_weekly_{start_date}.csv",
                        mimetype="text/csv",
                    )

        elif report_type == "monthly":
            if date_str:
                target_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                target_date = datetime.now()

            year_month = target_date.strftime("%Y-%m")
            attendance_files = [
                f
                for f in ATTENDANCE_DIR.glob("Attendance_*.csv")
                if year_month in f.name
            ]

            all_data = []
            for file_path in attendance_files:
                df = read_attendance_csv(file_path)
                if not df.empty:
                    all_data.append(df)

            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                formatted_file = format_csv_for_export(
                    combined_df, f"comprehensive_monthly_{year_month}"
                )
                if formatted_file:
                    return send_file(
                        formatted_file,
                        as_attachment=True,
                        download_name=f"comprehensive_monthly_{year_month}.csv",
                        mimetype="text/csv",
                    )

        elif report_type == "all":
            attendance_files = list(ATTENDANCE_DIR.glob("Attendance_*.csv"))
            all_data = []

            for file_path in attendance_files:
                df = read_attendance_csv(file_path)
                if not df.empty:
                    all_data.append(df)

            if all_data:
                combined_df = pd.concat(all_data, ignore_index=True)
                formatted_file = format_csv_for_export(
                    combined_df, "comprehensive_all_time"
                )
                if formatted_file:
                    return send_file(
                        formatted_file,
                        as_attachment=True,
                        download_name="comprehensive_all_time.csv",
                        mimetype="text/csv",
                    )

        return "No data available", 404

    except Exception as e:
        print(f"Error generating comprehensive report: {e}")
        return "Error generating report", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
