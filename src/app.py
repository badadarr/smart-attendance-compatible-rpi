from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd
import os
from datetime import datetime, date, timedelta  # Import timedelta for date range
import json
from pathlib import Path

# Define paths relative to project root
BASE_DIR = Path(__file__).parent.parent  # Go up one level from src/
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
ATTENDANCE_DIR = BASE_DIR / "Attendance"
LOG_DIR = BASE_DIR / "logs"  # Added for consistency

app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))

# Create necessary directories
ATTENDANCE_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)  # Ensure log directory exists


# Helper function to read attendance CSV with robust column handling
def read_attendance_csv(file_path):
    try:
        df = pd.read_csv(file_path)
        # Ensure all expected columns exist, fill missing with empty string or default
        expected_cols = [
            "NAME",
            "TIME",
            "DATE",
            "STATUS",
            "WORK_HOURS",
            "CONFIDENCE",
            "QUALITY",
            "FLAGS",
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
    return render_template("index.html")


@app.route("/daily_attendance")
def daily_attendance():
    selected_date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))

    attendance_file_path = ATTENDANCE_DIR / f"Attendance_{selected_date}.csv"

    data = {
        "date": selected_date,
        "has_data": False,
        "total_entries": 0,
        "unique_attendees": 0,  # Changed from present_count to unique_attendees for daily view
        "attendance_data": [],
    }

    if os.path.exists(attendance_file_path):
        df = read_attendance_csv(attendance_file_path)
        if not df.empty:
            data["has_data"] = True
            data["total_entries"] = len(df)
            # Count unique names who have any "Clock In" or "Clock Out" entries today
            data["unique_attendees"] = df["NAME"].nunique()
            data["attendance_data"] = df.to_dict("records")
        else:
            print(f"File {attendance_file_path} exists but is empty or unreadable.")

    return render_template("daily_attendance.html", data=data)


@app.route("/statistics")
def statistics():
    attendance_files = [
        f
        for f in os.listdir(ATTENDANCE_DIR)
        if f.startswith("Attendance_") and f.endswith(".csv")
    ]

    stats_data = {
        "has_data": False,
        "total_users_registered": 0,  # Total unique users across all records
        "total_attendance_days": 0,  # Total days with attendance files
        "average_work_hours": "00:00",
        "attendance_patterns": [],
        "longest_work_day": {"name": "N/A", "hours": "00:00", "date": "N/A"},
        "most_active_user": {"name": "N/A", "records": 0},
    }

    if attendance_files:
        try:
            all_data_frames = []
            for file_name in attendance_files:
                df = read_attendance_csv(ATTENDANCE_DIR / file_name)
                if not df.empty:
                    all_data_frames.append(df)

            if all_data_frames:
                combined_df = pd.concat(all_data_frames, ignore_index=True)
                stats_data["has_data"] = True
                stats_data["total_attendance_days"] = combined_df["DATE"].nunique()
                stats_data["total_users_registered"] = combined_df["NAME"].nunique()

                # Calculate average work hours across all valid "Clock Out" entries
                # This assumes 'WORK_HOURS' column is reliable and always HH:MM format
                valid_work_hours = combined_df[
                    combined_df["WORK_HOURS"].str.contains(":")
                    & (combined_df["WORK_HOURS"] != "00:00")
                ]

                total_hours_decimal = 0.0
                num_work_hour_entries = 0

                # Convert 'WORK_HOURS' to decimal hours
                for wh_str in valid_work_hours[
                    "WORK_HOURS"
                ].unique():  # Use unique to avoid double counting per record if multiple clock-outs for same day
                    try:
                        h, m = map(int, wh_str.split(":"))
                        total_hours_decimal += h + m / 60.0
                        num_work_hour_entries += 1
                    except ValueError:
                        continue  # Skip invalid format

                if num_work_hour_entries > 0:
                    avg_hours_decimal = total_hours_decimal / num_work_hour_entries
                    avg_hours_int = int(avg_hours_decimal)
                    avg_minutes_int = int((avg_hours_decimal - avg_hours_int) * 60)
                    stats_data["average_work_hours"] = (
                        f"{avg_hours_int:02d}:{avg_minutes_int:02d}"
                    )

                # Calculate attendance patterns based on days with any record
                days_attended = (
                    combined_df.groupby("NAME")["DATE"]
                    .nunique()
                    .reset_index(name="Days Attended")
                )
                total_entries_per_person = (
                    combined_df.groupby("NAME").size().reset_index(name="Total Entries")
                )

                attendance_patterns = days_attended.merge(
                    total_entries_per_person, on="NAME", how="left"
                )
                attendance_patterns.columns = ["Name", "Days Attended", "Total Entries"]

                # Calculate attendance rate based on days attended vs total attendance days
                if stats_data["total_attendance_days"] > 0:
                    attendance_patterns["Attendance Rate (%)"] = (
                        attendance_patterns["Days Attended"]
                        / stats_data["total_attendance_days"]
                        * 100
                    ).round(2)
                else:
                    attendance_patterns["Attendance Rate (%)"] = 0.0

                attendance_patterns = attendance_patterns.fillna(
                    0
                )  # Fill NaN from merge
                attendance_patterns["Total Entries"] = attendance_patterns[
                    "Total Entries"
                ].astype(int)

                stats_data["attendance_patterns"] = attendance_patterns.sort_values(
                    "Days Attended", ascending=False
                ).to_dict("records")

                # Longest work day calculation
                if "WORK_HOURS" in combined_df.columns:
                    combined_df["WORK_HOURS_DECIMAL"] = combined_df["WORK_HOURS"].apply(
                        lambda x: (
                            int(x.split(":")[0]) + int(x.split(":")[1]) / 60.0
                            if isinstance(x, str) and ":" in x
                            else 0.0
                        )
                    )
                    longest_day_row = combined_df.loc[
                        combined_df["WORK_HOURS_DECIMAL"].idxmax()
                    ]
                    stats_data["longest_work_day"] = {
                        "name": longest_day_row["NAME"],
                        "hours": longest_day_row["WORK_HOURS"],
                        "date": longest_day_row["DATE"],
                    }

                # Most active user (based on total entries)
                if not combined_df.empty:
                    most_active_user_name = combined_df["NAME"].value_counts().idxmax()
                    most_active_user_count = combined_df["NAME"].value_counts().max()
                    stats_data["most_active_user"] = {
                        "name": most_active_user_name,
                        "records": int(most_active_user_count),
                    }

        except Exception as e:
            print(f"Error generating statistics: {e}")
            import traceback

            traceback.print_exc()  # Print full traceback for debugging

    return render_template("statistics.html", data=stats_data)


@app.route("/download_csv")
def download_csv():
    date_str = request.args.get("date")
    if date_str:
        file_path = ATTENDANCE_DIR / f"Attendance_{date_str}.csv"
        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f"attendance_{date_str}.csv",
                mimetype="text/csv",  # Specify mimetype
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

                days_attended = (
                    combined_df.groupby("NAME")["DATE"]
                    .nunique()
                    .reset_index(name="Days Attended")
                )
                total_entries_per_person = (
                    combined_df.groupby("NAME").size().reset_index(name="Total Entries")
                )

                attendance_patterns = days_attended.merge(
                    total_entries_per_person, on="NAME", how="left"
                )
                attendance_patterns.columns = ["Name", "Days Attended", "Total Entries"]

                if total_attendance_days > 0:
                    attendance_patterns["Attendance Rate (%)"] = (
                        attendance_patterns["Days Attended"]
                        / total_attendance_days
                        * 100
                    ).round(2)
                else:
                    attendance_patterns["Attendance Rate (%)"] = 0.0

                attendance_patterns = attendance_patterns.fillna(0)
                attendance_patterns["Total Entries"] = attendance_patterns[
                    "Total Entries"
                ].astype(int)

                temp_file = "temp_attendance_patterns.csv"
                attendance_patterns.to_csv(temp_file, index=False)

                return send_file(
                    temp_file,
                    as_attachment=True,
                    download_name="attendance_patterns.csv",
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
        "unique_attendees": 0,  # Changed from present_count
        "last_entry": None,
    }

    if os.path.exists(attendance_file_path):
        df = read_attendance_csv(attendance_file_path)
        if not df.empty:
            status["total_entries"] = len(df)
            status["unique_attendees"] = df["NAME"].nunique()

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
    """Dashboard with attendance analysis"""
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
                "last_backup": "None",  # This would need a separate backup script/logic
            },
        },
        "analytics_charts": None,  # Placeholder for future chart data
    }

    try:
        # Get today's summary
        today_file = ATTENDANCE_DIR / f"Attendance_{today}.csv"
        if today_file.exists():
            df_today = read_attendance_csv(today_file)

            if not df_today.empty:
                unique_people_today = df_today["NAME"].nunique()
                total_entries_today = len(df_today)

                # Top attendees based on total entries today
                top_attendees_counts = df_today["NAME"].value_counts().head(5)
                top_attendees_list = [
                    {"name": name, "count": count}
                    for name, count in top_attendees_counts.items()
                ]

                dashboard_data["today_summary"] = {
                    "total_unique_attendees": unique_people_today,
                    "total_entries": total_entries_today,
                    "attendance_rate": (
                        (unique_people_today / max(df_today["NAME"].nunique(), 1)) * 100
                        if df_today["NAME"].nunique() > 0
                        else 0
                    ),
                    "new_registrations": 0,  # This would require comparing with a registered users list (e.g., from add_faces_rpi data)
                    "top_attendees": top_attendees_list,
                }

                # Get recent activity (last 10 entries)
                recent_entries = df_today.tail(10).to_dict("records")
                dashboard_data["recent_activity"] = recent_entries
            else:
                print(f"File {today_file} exists but is empty for dashboard summary.")

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


@app.route("/security")
def security_dashboard():
    """Security monitoring dashboard"""
    security_data = {
        "suspicious_activities": [],
        "quality_metrics": {},
        "fraud_patterns": {},
        "system_alerts": [],
        "daily_statistics": {},
    }

    try:
        # Read suspicious activity logs
        current_month = datetime.now().strftime("%Y-%m")
        log_file = LOG_DIR / f"suspicious_activities_{current_month}.log"

        if log_file.exists():
            with open(log_file, "r") as f:
                lines = f.readlines()
                # Parse log lines to dictionary for easier display
                for line in lines[-100:]:  # Show last 100 entries for dashboard
                    try:
                        parts = line.strip().split(" | ")
                        if len(parts) >= 3:
                            log_entry = {
                                "timestamp": parts[0],
                                "name": parts[1],
                                "flags": parts[2],
                            }
                            if len(parts) > 3:  # Check for additional_info JSON
                                try:
                                    log_entry["additional_info"] = json.loads(parts[3])
                                except json.JSONDecodeError:
                                    log_entry["additional_info"] = {
                                        "raw": parts[3]
                                    }  # Fallback if not valid JSON
                            security_data["suspicious_activities"].append(log_entry)
                    except Exception as e:
                        print(f"Error parsing log line: {line.strip()} - {e}")
                        continue

        security_data["suspicious_activities"].reverse()  # Show most recent first

        # Analyze attendance files for quality metrics
        attendance_files = list(ATTENDANCE_DIR.glob("Attendance_*.csv"))
        total_records_processed = 0
        quality_scores = []
        confidence_scores = []
        flagged_records_count = 0

        for file in attendance_files:
            df = read_attendance_csv(file)
            if df.empty:
                continue

            total_records_processed += len(df)

            # Use .loc to avoid SettingWithCopyWarning
            if "CONFIDENCE" in df.columns:
                confidence_scores.extend(
                    [
                        float(x)
                        for x in df["CONFIDENCE"].dropna()
                        if str(x).replace(".", "", 1).isdigit()
                    ]
                )
            if "QUALITY" in df.columns:
                quality_scores.extend(
                    [
                        float(x)
                        for x in df["QUALITY"].dropna()
                        if str(x).replace(".", "", 1).isdigit()
                    ]
                )
            if "FLAGS" in df.columns:
                flagged_records_count += len(
                    df[df["FLAGS"].astype(str).str.strip() != ""]
                )  # Count non-empty flags

        # Calculate quality metrics
        if quality_scores:
            security_data["quality_metrics"] = {
                "average_quality": round(np.mean(quality_scores), 3),
                "min_quality": round(np.min(quality_scores), 3),
                "max_quality": round(np.max(quality_scores), 3),
                "low_quality_count": len([q for q in quality_scores if q < 0.6]),
            }

        if confidence_scores:
            security_data["quality_metrics"].update(
                {
                    "average_confidence": round(np.mean(confidence_scores), 3),
                    "min_confidence": round(np.min(confidence_scores), 3),
                    "max_confidence": round(np.max(confidence_scores), 3),
                    "low_confidence_count": len(
                        [c for c in confidence_scores if c < 0.7]
                    ),
                }
            )

        # Calculate fraud patterns
        security_data["fraud_patterns"] = {
            "total_records_analyzed": total_records_processed,
            "flagged_records": flagged_records_count,
            "fraud_percentage": round(
                (flagged_records_count / max(total_records_processed, 1)) * 100, 2
            ),
            "suspicious_activities_logged": len(security_data["suspicious_activities"]),
        }

        # Generate system alerts
        alerts = []
        if security_data["fraud_patterns"]["fraud_percentage"] > 5:
            alerts.append(
                {
                    "level": "warning",
                    "message": f"High fraud rate detected: {security_data['fraud_patterns']['fraud_percentage']}% of records flagged.",
                }
            )
        if security_data["quality_metrics"].get("low_quality_count", 0) > 10:
            alerts.append(
                {
                    "level": "info",
                    "message": f"Many low quality face detections: {security_data['quality_metrics']['low_quality_count']} instances.",
                }
            )
        if security_data["quality_metrics"].get("average_confidence", 0) < 0.7:
            alerts.append(
                {
                    "level": "warning",
                    "message": f"Average recognition confidence is low: {security_data['quality_metrics']['average_confidence']:.2f}. Consider retraining.",
                }
            )
        security_data["system_alerts"] = alerts

        # Daily statistics for security (e.g., daily flagged records)
        daily_flagged = {}
        for file in attendance_files:
            df = read_attendance_csv(file)
            if df.empty:
                continue
            file_date = file.stem.replace("Attendance_", "")
            if "FLAGS" in df.columns:
                daily_flagged[file_date] = len(
                    df[df["FLAGS"].astype(str).str.strip() != ""]
                )
            else:
                daily_flagged[file_date] = 0
        security_data["daily_statistics"]["flagged_records_by_date"] = sorted(
            daily_flagged.items()
        )

    except Exception as e:
        print(f"Error generating security data: {e}")
        import traceback

        traceback.print_exc()

    return render_template("security.html", data=security_data)


@app.route("/api/security/export")
def export_security_report():
    """Export security analysis report"""
    try:
        report_data_frames = []
        attendance_files = list(ATTENDANCE_DIR.glob("Attendance_*.csv"))

        for file in attendance_files:
            df = read_attendance_csv(file)
            if df.empty:
                continue

            # Add security analysis columns dynamically
            df["HAS_FLAGS"] = df["FLAGS"].apply(
                lambda x: "Yes" if str(x).strip() else "No"
            )
            df["QUALITY_CATEGORY"] = df["QUALITY"].apply(
                lambda x: (
                    "High"
                    if str(x).replace(".", "", 1).isdigit() and float(x) >= 0.8
                    else (
                        "Medium"
                        if str(x).replace(".", "", 1).isdigit() and float(x) >= 0.6
                        else (
                            "Low"
                            if str(x).replace(".", "", 1).isdigit() and float(x) > 0
                            else "Unknown"
                        )
                    )
                )
            )
            df["CONFIDENCE_CATEGORY"] = df["CONFIDENCE"].apply(
                lambda x: (
                    "High"
                    if str(x).replace(".", "", 1).isdigit() and float(x) >= 0.8
                    else (
                        "Medium"
                        if str(x).replace(".", "", 1).isdigit() and float(x) >= 0.6
                        else (
                            "Low"
                            if str(x).replace(".", "", 1).isdigit() and float(x) > 0
                            else "Unknown"
                        )
                    )
                )
            )
            report_data_frames.append(df)

        if report_data_frames:
            combined_df = pd.concat(report_data_frames, ignore_index=True)

            # Select and reorder columns for clarity in the report
            final_columns = [
                "NAME",
                "DATE",
                "TIME",
                "STATUS",
                "WORK_HOURS",
                "CONFIDENCE",
                "CONFIDENCE_CATEGORY",
                "QUALITY",
                "QUALITY_CATEGORY",
                "FLAGS",
                "HAS_FLAGS",
            ]
            # Keep only columns that exist in the combined_df
            final_columns = [col for col in final_columns if col in combined_df.columns]

            temp_file = "temp_security_report.csv"
            combined_df[final_columns].to_csv(temp_file, index=False)

            return send_file(
                temp_file,
                as_attachment=True,
                download_name=f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mimetype="text/csv",
            )
        else:
            return "No data available", 404

    except Exception as e:
        print(f"Error generating security report: {e}")
        import traceback

        traceback.print_exc()
        return f"Error generating report: {e}", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
