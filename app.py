from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import pandas as pd
import os
from datetime import datetime, date
import json

app = Flask(__name__)

# Create necessary directories
if not os.path.exists("Attendance"):
    os.makedirs("Attendance")

if not os.path.exists("templates"):
    os.makedirs("templates")

if not os.path.exists("static"):
    os.makedirs("static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/daily_attendance")
def daily_attendance():
    selected_date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    formatted_date = selected_date_obj.strftime(
        "%Y-%m-%d"
    )  # Menggunakan format yang sesuai dengan file CSV

    attendance_file_path = f"Attendance/Attendance_{formatted_date}.csv"

    data = {
        "date": selected_date,
        "formatted_date": formatted_date,
        "has_data": False,
        "total_entries": 0,
        "present_count": 0,  # Changed from clock_ins/clock_outs to present_count
        "attendance_data": [],
    }

    if os.path.exists(attendance_file_path):
        try:
            df = pd.read_csv(attendance_file_path)
            data["has_data"] = True
            data["total_entries"] = len(df)
            data["present_count"] = len(
                df[df["STATUS"] == "Present"]
            )  # Count Present status
            data["attendance_data"] = df.to_dict("records")
        except Exception as e:
            print(f"Error reading attendance file: {e}")

    return render_template("daily_attendance.html", data=data)


@app.route("/statistics")
def statistics():
    attendance_files = [
        f
        for f in os.listdir("Attendance")
        if f.startswith("Attendance_") and f.endswith(".csv")
    ]

    stats_data = {
        "has_data": False,
        "total_students": 0,
        "total_days": 0,
        "most_common_time": "No data",  # Changed from separate clock_in/clock_out
        "attendance_patterns": [],
    }

    if attendance_files:
        try:
            all_data = []
            for file in attendance_files:
                df = pd.read_csv(os.path.join("Attendance", file))
                all_data.append(df)

            if all_data:
                combined_df = pd.concat(all_data)
                stats_data["has_data"] = True
                stats_data["total_students"] = combined_df["NAME"].nunique()
                stats_data["total_days"] = len(
                    attendance_files
                )  # Calculate most common time (for Present status)
                present_times = combined_df[combined_df["STATUS"] == "Present"]["TIME"]

                if not present_times.empty:
                    stats_data["most_common_time"] = present_times.mode().iloc[
                        0
                    ]  # Calculate attendance patterns
                days_present = (
                    combined_df.groupby("NAME")["DATE"].nunique().reset_index()
                )
                present_count = (
                    combined_df[combined_df["STATUS"] == "Present"]
                    .groupby("NAME")
                    .size()
                    .reset_index(name="Total Present")
                )

                attendance_patterns = days_present.merge(
                    present_count, on="NAME", how="left"
                )

                attendance_patterns.columns = [
                    "Name",
                    "Days Present",
                    "Total Present",
                ]
                attendance_patterns = attendance_patterns.fillna(0)
                attendance_patterns["Total Present"] = attendance_patterns[
                    "Total Present"
                ].astype(int)
                attendance_patterns["Attendance Rate"] = (
                    attendance_patterns["Days Present"] / stats_data["total_days"] * 100
                ).round(2)

                attendance_patterns = attendance_patterns.sort_values(
                    "Days Present", ascending=False
                )
                stats_data["attendance_patterns"] = attendance_patterns.to_dict(
                    "records"
                )

        except Exception as e:
            print(f"Error generating statistics: {e}")

    return render_template("statistics.html", data=stats_data)


@app.route("/download_csv")
def download_csv():
    date_str = request.args.get("date")
    if date_str:
        selected_date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = selected_date_obj.strftime(
            "%Y-%m-%d"
        )  # Format tanggal yang sesuai dengan file CSV
        file_path = f"Attendance/Attendance_{formatted_date}.csv"

        if os.path.exists(file_path):
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f"attendance_{formatted_date}.csv",
            )

    return "File not found", 404


@app.route("/download_patterns")
def download_patterns():
    # Generate patterns CSV and send it
    attendance_files = [
        f
        for f in os.listdir("Attendance")
        if f.startswith("Attendance_") and f.endswith(".csv")
    ]

    if attendance_files:
        try:
            all_data = []
            for file in attendance_files:
                df = pd.read_csv(os.path.join("Attendance", file))
                all_data.append(df)

            combined_df = pd.concat(all_data)
            total_days = len(attendance_files)

            days_present = combined_df.groupby("NAME")["DATE"].nunique().reset_index()
            present_count = (
                combined_df[combined_df["STATUS"] == "Present"]
                .groupby("NAME")
                .size()
                .reset_index(name="Total Present")
            )

            attendance_patterns = days_present.merge(
                present_count, on="NAME", how="left"
            )

            attendance_patterns.columns = [
                "Name",
                "Days Present",
                "Total Present",
            ]
            attendance_patterns = attendance_patterns.fillna(0)
            attendance_patterns["Total Present"] = attendance_patterns[
                "Total Present"
            ].astype(int)
            attendance_patterns["Attendance Rate"] = (
                attendance_patterns["Days Present"] / total_days * 100
            ).round(2)

            # Save to temporary file
            temp_file = "temp_attendance_patterns.csv"
            attendance_patterns.to_csv(temp_file, index=False)

            return send_file(
                temp_file, as_attachment=True, download_name="attendance_patterns.csv"
            )

        except Exception as e:
            print(f"Error generating patterns: {e}")

    return "No data available", 404


@app.route("/api/attendance_status")
def get_attendance_status():
    """API endpoint to get current attendance status for real-time updates"""
    today = datetime.now().strftime("%Y-%m-%d")  # Format tanggal sesuai dengan file CSV
    attendance_file_path = f"Attendance/Attendance_{today}.csv"

    status = {
        "date": today,
        "total_entries": 0,
        "present_count": 0,
        "last_entry": None,
    }

    if os.path.exists(attendance_file_path):
        try:
            df = pd.read_csv(attendance_file_path)
            status["total_entries"] = len(df)
            status["present_count"] = len(df[df["STATUS"] == "Present"])

            if not df.empty:
                last_row = df.iloc[-1]
                status["last_entry"] = {
                    "name": last_row["NAME"],
                    "time": last_row["TIME"],
                    "status": last_row["STATUS"],
                }
        except Exception as e:
            print(f"Error reading attendance file: {e}")

    return jsonify(status)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
