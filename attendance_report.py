
import pandas as pd
from pathlib import Path

from database_repository import get_attendance


SELECTED_DATE = "2026-11-04"
REPORT_FILE = Path("data/daily_attendance_report.csv")


def generate_attendance_report(selected_date=SELECTED_DATE):

    print("\n========== LOADING POSTGRESQL ATTENDANCE DATA ==========")

    attendance = get_attendance()

    if attendance.empty:
        print("No attendance records available in PostgreSQL.")
        return

    required_columns = [
        "employee_id",
        "attendance_date",
        "shift",
        "attendance_status",
        "check_in",
        "check_out"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in attendance.columns
    ]

    if missing_columns:
        print("ERROR: Missing attendance columns:", missing_columns)
        return

    attendance["attendance_date"] = pd.to_datetime(
        attendance["attendance_date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    daily_data = attendance[
        attendance["attendance_date"] == selected_date
    ].copy()

    print("\n========== DAILY ATTENDANCE REPORT ==========")
    print("Selected Date:", selected_date)

    if daily_data.empty:
        print("No attendance records found for this date.")
        return

    total_employees = len(daily_data)

    present = (
        daily_data["attendance_status"] == "Present"
    ).sum()

    absent = (
        daily_data["attendance_status"] == "Absent"
    ).sum()

    leave = (
        daily_data["attendance_status"] == "Leave"
    ).sum()

    attendance_percentage = round(
        present / total_employees * 100,
        2
    )

    print("\nTotal Employees:", total_employees)
    print("Present:", present)
    print("Absent:", absent)
    print("On Leave:", leave)

    print(
        "Attendance Percentage:",
        str(attendance_percentage) + "%"
    )

    print("\n========== SHIFT-WISE ATTENDANCE ==========")

    shift_report = (
        daily_data
        .groupby(["shift", "attendance_status"])
        .size()
        .unstack(fill_value=0)
    )

    print(shift_report.to_string())

    print("\n========== EMPLOYEE ATTENDANCE DETAILS ==========")

    print(
        daily_data[required_columns].to_string(index=False)
    )

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    daily_data.to_csv(
        REPORT_FILE,
        index=False
    )

    print("\nAttendance report exported to:", REPORT_FILE)
    print("Master attendance data was read from PostgreSQL.")
    print("No PostgreSQL records were modified.")


if __name__ == "__main__":
    generate_attendance_report()
