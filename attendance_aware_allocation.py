
import pandas as pd

from database_repository import (
    get_employees,
    get_attendance
)


def check_employee_availability(selected_date="2026-11-04"):

    # -------------------------------------------------
    # STEP 1: LOAD DATA FROM POSTGRESQL
    # -------------------------------------------------

    print("\n========== LOADING POSTGRESQL DATA ==========")

    employees = get_employees()
    attendance = get_attendance()

    if employees.empty:
        print("No employee records found.")
        return

    if attendance.empty:
        print("No attendance records found.")
        return

    # -------------------------------------------------
    # STEP 2: NORMALIZE DATE AND STATUS
    # -------------------------------------------------

    attendance["attendance_date"] = pd.to_datetime(
        attendance["attendance_date"]
    ).dt.strftime("%Y-%m-%d")

    selected_date = pd.to_datetime(
        selected_date
    ).strftime("%Y-%m-%d")

    attendance["attendance_status"] = (
        attendance["attendance_status"]
        .astype(str)
        .str.strip()
    )

    employees = employees[
        employees["status"].astype(str).str.lower() == "active"
    ].copy()

    # -------------------------------------------------
    # STEP 3: FILTER ATTENDANCE FOR SELECTED DATE
    # -------------------------------------------------

    daily_attendance = attendance[
        attendance["attendance_date"] == selected_date
    ].copy()

    # Match using employee ID AND shift
    availability = employees.merge(
        daily_attendance[
            ["employee_id", "shift", "attendance_status"]
        ],
        on=["employee_id", "shift"],
        how="left"
    )

    # -------------------------------------------------
    # STEP 4: CLASSIFY EMPLOYEE AVAILABILITY
    # -------------------------------------------------

    availability["availability_status"] = (
        availability["attendance_status"]
        .map({
            "Present": "Available",
            "Absent": "Unavailable",
            "Leave": "Unavailable"
        })
        .fillna("Attendance Missing")
    )

    available_employees = availability[
        availability["availability_status"] == "Available"
    ].copy()

    unavailable_employees = availability[
        availability["availability_status"] == "Unavailable"
    ].copy()

    missing_attendance = availability[
        availability["availability_status"] == "Attendance Missing"
    ].copy()

    # -------------------------------------------------
    # STEP 5: DISPLAY AVAILABLE EMPLOYEES
    # -------------------------------------------------

    print("\n========== ATTENDANCE-AWARE ALLOCATION ==========")

    print("\nSelected date:", selected_date)

    print("\n--- AVAILABLE EMPLOYEES ---")

    if available_employees.empty:
        print("No available employees.")
    else:
        print(
            available_employees[
                ["employee_id", "employee_name", "shift"]
            ].to_string(index=False)
        )

    # -------------------------------------------------
    # STEP 6: DISPLAY UNAVAILABLE EMPLOYEES
    # -------------------------------------------------

    print("\n--- UNAVAILABLE EMPLOYEES ---")

    if unavailable_employees.empty:
        print("No unavailable employees.")
    else:
        print(
            unavailable_employees[
                [
                    "employee_id",
                    "employee_name",
                    "shift",
                    "attendance_status"
                ]
            ].to_string(index=False)
        )

    # -------------------------------------------------
    # STEP 7: DISPLAY MISSING ATTENDANCE
    # -------------------------------------------------

    print("\n--- EMPLOYEES WITH MISSING ATTENDANCE ---")

    if missing_attendance.empty:
        print("No missing attendance records.")
    else:
        print(
            missing_attendance[
                ["employee_id", "employee_name", "shift"]
            ].to_string(index=False)
        )

    # -------------------------------------------------
    # STEP 8: SUMMARY
    # -------------------------------------------------

    print("\n========== AVAILABILITY SUMMARY ==========")

    print("Total active employees:", len(employees))
    print("Available employees:", len(available_employees))
    print("Unavailable employees:", len(unavailable_employees))
    print("Attendance missing:", len(missing_attendance))

    print("\nAttendance data was read from PostgreSQL.")
    print("No PostgreSQL records were modified.")

    print("\n========== AVAILABILITY FILTER COMPLETED ==========")


if __name__ == "__main__":
    check_employee_availability()
