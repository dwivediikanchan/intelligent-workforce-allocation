
import pandas as pd

from database_repository import (
    get_employees,
    get_attendance,
    get_allocations,
    get_stations
)


def generate_daily_summary(allocation_date="2026-11-04"):

    print("\n========== LOADING POSTGRESQL DATA ==========")

    # ==========================================
    # STEP 1: LOAD DATABASE TABLES
    # ==========================================

    employees = get_employees()
    attendance = get_attendance()
    allocations = get_allocations()
    stations = get_stations()

    if employees.empty:
        print("No employee records found.")
        return

    if stations.empty:
        print("No station records found.")
        return

    required_employee_columns = {
        "employee_id", "employee_name", "shift", "status"
    }

    required_attendance_columns = {
        "employee_id", "attendance_date",
        "shift", "attendance_status"
    }

    required_allocation_columns = {
        "employee_id", "station_id",
        "shift", "status", "allocation_date"
    }

    if required_employee_columns - set(employees.columns):
        raise ValueError("Employee table is missing required columns.")

    if required_attendance_columns - set(attendance.columns):
        raise ValueError("Attendance table is missing required columns.")

    if required_allocation_columns - set(allocations.columns):
        raise ValueError("Allocation table is missing required columns.")

    print("Employee data loaded from PostgreSQL.")
    print("Attendance data loaded from PostgreSQL.")
    print("Allocation data loaded from PostgreSQL.")
    print("Station master data loaded from PostgreSQL.")

    # ==========================================
    # STEP 2: FILTER SELECTED DATE
    # ==========================================

    attendance["attendance_date"] = pd.to_datetime(
        attendance["attendance_date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    allocations["allocation_date"] = pd.to_datetime(
        allocations["allocation_date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    daily_attendance = attendance[
        attendance["attendance_date"] == allocation_date
    ].copy()

    daily_allocations = allocations[
        (allocations["allocation_date"] == allocation_date)
        & (allocations["status"] == "Allocated")
    ].copy()

    active_employees = employees[
        employees["status"].astype(str).str.lower() == "active"
    ].copy()

    print("Selected date:", allocation_date)

    # ==========================================
    # STEP 3: BUILD DAILY WORKFORCE ROSTER
    # ==========================================

    attendance_duplicates = daily_attendance.duplicated(
        subset=["employee_id", "shift"],
        keep=False
    )

    if attendance_duplicates.any():
        raise ValueError(
            "Duplicate attendance records found for an employee and shift."
        )

    allocation_duplicates = daily_allocations.duplicated(
        subset=["employee_id", "shift"],
        keep=False
    )

    if allocation_duplicates.any():
        raise ValueError(
            "Multiple active allocations found for an employee and shift."
        )

    roster = active_employees.merge(
        daily_attendance[
            ["employee_id", "shift", "attendance_status"]
        ],
        on=["employee_id", "shift"],
        how="left"
    )

    roster = roster.rename(
        columns={"attendance_status": "daily_attendance"}
    )

    # Add allocation information to the workforce roster.
    allocation_columns = [
        "employee_id", "shift", "station_id"
    ]

    if "skill_score" in daily_allocations.columns:
        allocation_columns.append("skill_score")

    roster = roster.merge(
        daily_allocations[allocation_columns],
        on=["employee_id", "shift"],
        how="left"
    )

    # ==========================================
    # STEP 4: DETERMINE EMPLOYEE STATUS
    # ==========================================

    def determine_status(row):

        attendance_status = row["daily_attendance"]

        if pd.isna(attendance_status):
            return "Attendance Missing"

        attendance_status = str(attendance_status).strip().lower()

        if attendance_status == "absent":
            return "Absent"

        if attendance_status == "leave":
            return "Leave"

        if attendance_status == "present":

            if pd.notna(row["station_id"]):
                return "Allocated"

            return "Unallocated"

        return "Other Attendance Status"

    roster["status"] = roster.apply(
        determine_status,
        axis=1
    )

    roster["station_id"] = roster["station_id"].fillna("Not Assigned")

    if "skill_score" in roster.columns:
        roster["skill_score"] = roster["skill_score"].fillna(0)

    print("\n========== DAILY ALLOCATION SUMMARY ==========")

    # ==========================================
    # STEP 5: OVERALL SUMMARY
    # ==========================================

    total = len(roster)

    allocated = (roster["status"] == "Allocated").sum()
    unallocated = (roster["status"] == "Unallocated").sum()
    absent = (roster["status"] == "Absent").sum()
    leave = (roster["status"] == "Leave").sum()

    attendance_missing = (
        roster["status"] == "Attendance Missing"
    ).sum()

    print("\n--- Overall Summary ---")
    print("Total Employees:", total)
    print("Allocated:", allocated)
    print("Unallocated:", unallocated)
    print("Absent:", absent)
    print("On Leave:", leave)
    print("Attendance Missing:", attendance_missing)

    # ==========================================
    # STEP 6: SHIFT-WISE SUMMARY
    # ==========================================

        # ==========================================
    # STEP 6: SHIFT-WISE SUMMARY
    # ==========================================

    print("\n--- Shift-wise Summary ---")

    status_columns = [
        "Allocated",
        "Unallocated",
        "Absent",
        "Leave",
        "Attendance Missing"
    ]

    shift_summary = pd.crosstab(
        roster["shift"],
        roster["status"]
    )

    shift_summary = shift_summary.reindex(
        columns=status_columns,
        fill_value=0
    )

    print(shift_summary.to_string(
    justify="right",
    col_space=15
))
    # ==========================================
    # STEP 7: STATION-WISE ALLOCATION
    # ==========================================

    print("\n--- Station-wise Allocation ---")

    allocated_records = roster[
        roster["status"] == "Allocated"
    ].copy()

    station_summary = allocated_records.groupby(
        ["station_id", "shift"]
    ).size().reset_index(
        name="employee_count"
    )

    if station_summary.empty:
        print("No station allocations available.")
    else:
        print(station_summary.to_string(index=False))

    # ==========================================
    # STEP 8: STATION UTILIZATION
    # ==========================================

    print("\n--- Station Utilization ---")

    utilization_records = []

    shifts = sorted(
        roster["shift"].dropna().unique().tolist()
    )

    for _, station in stations.iterrows():

        station_id = station["station_id"]
        capacity = station["capacity"]

        for shift in shifts:

            count = len(
                allocated_records[
                    (allocated_records["station_id"] == station_id)
                    & (allocated_records["shift"] == shift)
                ]
            )

            if pd.isna(capacity) or capacity <= 0:
                utilization = 0
                available_capacity = 0
            else:
                utilization = (count / capacity) * 100
                available_capacity = max(capacity - count, 0)

            print(
                f"{station_id} | {shift} | "
                f"{count}/{capacity} | "
                f"Utilization: {utilization:.1f}%"
            )

            utilization_records.append({
                "station_id": station_id,
                "station_name": station["station_name"],
                "shift": shift,
                "allocated_employees": count,
                "capacity": capacity,
                "available_capacity": available_capacity,
                "utilization_percentage": round(
                    utilization, 2
                )
            })

    utilization_report = pd.DataFrame(
        utilization_records
    )

    utilization_report.to_csv(
        "data/station_utilization_report.csv",
        index=False
    )

    print("\nStation utilization report saved successfully!")

    # ==========================================
    # STEP 9: MANAGER CAPACITY ALERTS
    # ==========================================

    print("\n========== MANAGER CAPACITY ALERTS ==========")

    full_stations = utilization_report[
        utilization_report["utilization_percentage"] >= 100
    ]

    if not full_stations.empty:

        for _, row in full_stations.iterrows():

            print(
                f"ALERT: {row['station_id']} is FULL "
                f"during {row['shift']} shift."
            )

    else:
        print("No stations are currently at full capacity.")

    print("\n========== ALERT CHECK COMPLETED ==========")

    # ==========================================
    # STEP 10: EMPLOYEE STATUS ALERTS
    # ==========================================

    print("\n========== EMPLOYEE STATUS ALERTS ==========")

    for _, employee in roster.iterrows():

        name = employee["employee_name"]
        employee_id = employee["employee_id"]
        shift = employee["shift"]
        status = employee["status"]

        if status == "Unallocated":
            print(
                f"ALERT: {name} ({employee_id}) "
                f"is present but not allocated during {shift} shift."
            )

        elif status == "Attendance Missing":
            print(
                f"ALERT: Attendance missing for "
                f"{name} ({employee_id}) during {shift} shift."
            )

        elif status == "Absent":
            print(
                f"INFO: {name} ({employee_id}) is absent."
            )

        elif status == "Leave":
            print(
                f"INFO: {name} ({employee_id}) is on leave."
            )

    print("\n========== EMPLOYEE ALERT CHECK COMPLETED ==========")

    # ==========================================
    # STEP 11: FINAL STATUS
    # ==========================================

    print("\nDaily workforce data: PostgreSQL")
    print("Attendance data: PostgreSQL")
    print("Allocation data: PostgreSQL")
    print("Station master data: PostgreSQL")
    print("PostgreSQL records modified: No")

    print("\n========== SUMMARY COMPLETED ==========")

    return utilization_report


if __name__ == "__main__":
    generate_daily_summary()
