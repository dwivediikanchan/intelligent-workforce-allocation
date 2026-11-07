
from database_repository import get_employees, get_attendance


def validate_attendance():

    print("\n========== LOADING POSTGRESQL DATA ==========")

    employees = get_employees()
    attendance = get_attendance()

    print("\n========== ATTENDANCE DATA VALIDATION ==========")

    if employees.empty:
        print("ERROR: No employee records found in PostgreSQL.")
        return

    if attendance.empty:
        print("ERROR: No attendance records found in PostgreSQL.")
        return

    required_employee_columns = ["employee_id"]

    required_attendance_columns = [
        "employee_id",
        "attendance_date",
        "shift",
        "attendance_status",
        "check_in",
        "check_out"
    ]

    missing_employee_columns = [
        col for col in required_employee_columns
        if col not in employees.columns
    ]

    missing_attendance_columns = [
        col for col in required_attendance_columns
        if col not in attendance.columns
    ]

    if missing_employee_columns or missing_attendance_columns:
        print("Missing employee columns:", missing_employee_columns)
        print("Missing attendance columns:", missing_attendance_columns)
        return

    errors = 0

    # 1. Employee ID validation
    valid_employee_ids = set(employees["employee_id"].astype(str))

    invalid_ids = attendance[
        ~attendance["employee_id"].astype(str).isin(valid_employee_ids)
    ]

    if invalid_ids.empty:
        print("PASS: All employee IDs are valid.")
    else:
        errors += len(invalid_ids)
        print("FAIL: Invalid employee IDs:")
        print(invalid_ids[["employee_id", "attendance_date"]].to_string(index=False))

    # 2. Attendance status validation
    valid_statuses = ["Present", "Absent", "Leave"]

    invalid_status = attendance[
        ~attendance["attendance_status"].isin(valid_statuses)
    ]

    if invalid_status.empty:
        print("PASS: All attendance statuses are valid.")
    else:
        errors += len(invalid_status)
        print("FAIL: Invalid attendance statuses:")
        print(invalid_status[["employee_id", "attendance_status"]].to_string(index=False))

    # 3. Shift validation
    valid_shifts = ["Morning", "Evening", "Night"]

    invalid_shift = attendance[
        ~attendance["shift"].isin(valid_shifts)
    ]

    if invalid_shift.empty:
        print("PASS: All attendance shifts are valid.")
    else:
        errors += len(invalid_shift)
        print("FAIL: Invalid shifts:")
        print(invalid_shift[["employee_id", "shift"]].to_string(index=False))

    # 4. Duplicate employee/date validation
    duplicates = attendance[
        attendance.duplicated(
            subset=["employee_id", "attendance_date"],
            keep=False
        )
    ]

    if duplicates.empty:
        print("PASS: No duplicate employee/date records found.")
    else:
        errors += len(duplicates)
        print("FAIL: Duplicate attendance records:")
        print(duplicates[["employee_id", "attendance_date"]].to_string(index=False))

    # 5. Present employee time validation
    present = attendance[
        attendance["attendance_status"] == "Present"
    ]

    missing_times = present[
        present["check_in"].isna()
        | present["check_out"].isna()
    ]

    if missing_times.empty:
        print("PASS: Present employees have check-in and check-out times.")
    else:
        errors += len(missing_times)
        print("FAIL: Missing attendance times:")
        print(missing_times[["employee_id", "check_in", "check_out"]].to_string(index=False))

    # Final result
    print("\n========== VALIDATION SUMMARY ==========")
    print("Total attendance records:", len(attendance))
    print("Validation errors:", errors)

    if errors == 0:
        print("RESULT: ALL ATTENDANCE VALIDATIONS PASSED.")
    else:
        print("RESULT: ATTENDANCE VALIDATION FAILED.")

    print("Master data was read from PostgreSQL.")
    print("No PostgreSQL records were modified.")


if __name__ == "__main__":
    validate_attendance()
