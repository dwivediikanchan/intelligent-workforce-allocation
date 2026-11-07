
import pandas as pd

from database_repository import get_employees, get_attendance


SELECTED_DATE = "2026-11-04"


def check_employee_availability(selected_date=SELECTED_DATE):

    print("\n========== LOADING POSTGRESQL DATA ==========")

    employees = get_employees()
    attendance = get_attendance()

    if employees.empty:
        print("ERROR: No employee records found in PostgreSQL.")
        return

    if attendance.empty:
        print("ERROR: No attendance records found in PostgreSQL.")
        return

    required_employee_columns = [
        "employee_id",
        "employee_name",
        "shift",
        "status"
    ]

    required_attendance_columns = [
        "employee_id",
        "attendance_date",
        "shift",
        "attendance_status"
    ]

    missing_employee_columns = [
        column for column in required_employee_columns
        if column not in employees.columns
    ]

    missing_attendance_columns = [
        column for column in required_attendance_columns
        if column not in attendance.columns
    ]

    if missing_employee_columns:
        print("Missing employee columns:", missing_employee_columns)
        return

    if missing_attendance_columns:
        print("Missing attendance columns:", missing_attendance_columns)
        return

    # Normalize attendance date
    attendance["attendance_date"] = pd.to_datetime(
        attendance["attendance_date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    # Get attendance for selected date
    daily_attendance = attendance[
        attendance["attendance_date"] == selected_date
    ].copy()

    print("\n========== EMPLOYEE AVAILABILITY REPORT ==========")
    print("Selected Date:", selected_date)

    # Match employee and shift
    availability = employees.merge(
        daily_attendance[
            ["employee_id", "shift", "attendance_status"]
        ],
        on=["employee_id", "shift"],
        how="left"
    )

    # Determine availability
    availability["availability"] = availability[
        "attendance_status"
    ].map({
        "Present": "Available",
        "Absent": "Unavailable",
        "Leave": "Unavailable"
    }).fillna("Attendance Missing")

    display_columns = [
        "employee_id",
        "employee_name",
        "shift",
        "status",
        "attendance_status",
        "availability"
    ]

    print("\n========== EMPLOYEE-WISE AVAILABILITY ==========")

    print(
        availability[display_columns].to_string(index=False)
    )

    print("\n========== AVAILABILITY SUMMARY ==========")

    availability_summary = (
        availability["availability"]
        .value_counts()
    )

    print(availability_summary.to_string())

    print("\n========== SHIFT-WISE AVAILABILITY ==========")

    shift_summary = (
        availability
        .groupby(["shift", "availability"])
        .size()
        .unstack(fill_value=0)
    )

    print(shift_summary.to_string())

    print("\nTotal employees:", len(availability))
    print(
        "Available employees:",
        (availability["availability"] == "Available").sum()
    )
    print(
        "Unavailable employees:",
        (availability["availability"] == "Unavailable").sum()
    )
    print(
        "Attendance missing:",
        (availability["availability"] == "Attendance Missing").sum()
    )

    print("\nMaster data was read from PostgreSQL.")
    print("No PostgreSQL records were modified.")


if __name__ == "__main__":
    check_employee_availability()
