
import pandas as pd

from database_repository import (
    get_employees,
    get_stations
)


def validate_daily_allocations():

    # ==========================================
    # STEP 1: LOAD DATA
    # ==========================================

    print("\n========== LOADING VALIDATION DATA ==========")

    allocations = pd.read_csv("data/daily_allocations.csv")
    stations = get_stations()
    employees = get_employees()

    if allocations.empty:
        print("ERROR: Daily allocation preview is empty.")
        return

    if stations.empty or employees.empty:
        print("ERROR: PostgreSQL master data is unavailable.")
        return

    print("Daily allocation preview: CSV")
    print("Station master data: PostgreSQL")
    print("Employee master data: PostgreSQL")

    print("\n========== DAILY ALLOCATION VALIDATION ==========")

    # ==========================================
    # STEP 2: DUPLICATE EMPLOYEE CHECK
    # ==========================================

    print("\n1. Duplicate Employee Check:")

    duplicates = allocations[
        allocations.duplicated(
            subset=["employee_id"],
            keep=False
        )
    ]

    if duplicates.empty:
        print("PASS: No duplicate employee allocations.")
    else:
        print("FAIL: Duplicate employee allocations found.")
        print(duplicates.to_string(index=False))

    # ==========================================
    # STEP 3: STATION CAPACITY CHECK
    # ==========================================

    print("\n2. Station Capacity Check:")

    allocated = allocations[
        allocations["status"] == "Allocated"
    ].copy()

    capacity_violations = []

    shifts = sorted(
        allocations["shift"].dropna().unique()
    )

    for _, station in stations.iterrows():

        station_id = station["station_id"]
        capacity = station["capacity"]

        for shift in shifts:

            count = len(
                allocated[
                    (allocated["station_id"] == station_id) &
                    (allocated["shift"] == shift)
                ]
            )

            if pd.isna(capacity):
                print(
                    f"FAIL: {station_id} {shift}: "
                    "Capacity is missing."
                )
                capacity_violations.append(
                    (station_id, shift)
                )

            elif count <= capacity:
                print(
                    f"PASS: {station_id} {shift}: "
                    f"{count}/{capacity}"
                )

            else:
                print(
                    f"FAIL: {station_id} {shift}: "
                    f"{count}/{capacity}"
                )
                capacity_violations.append(
                    (station_id, shift)
                )

    # ==========================================
    # STEP 4: UNAVAILABLE EMPLOYEE CHECK
    # ==========================================

    print("\n3. Availability Check:")

    unavailable = allocations[
        allocations["status"].isin(["Absent", "Leave"])
    ]

    invalid_unavailable = unavailable[
        unavailable["station_id"] != "Not Assigned"
    ]

    if invalid_unavailable.empty:
        print("PASS: Absent and leave employees are not allocated.")
    else:
        print("FAIL: An unavailable employee has an assignment.")
        print(invalid_unavailable.to_string(index=False))

    # ==========================================
    # STEP 5: ACTIVE EMPLOYEE COVERAGE CHECK
    # ==========================================

    print("\n4. Employee Coverage Check:")

    active_ids = set(
        employees.loc[
            employees["status"].astype(str).str.lower() == "active",
            "employee_id"
        ]
    )

    preview_ids = set(allocations["employee_id"])

    missing = active_ids - preview_ids
    unknown = preview_ids - active_ids

    if not missing:
        print("PASS: All active employees are included.")
    else:
        print("FAIL: Active employees missing from preview:")
        print(sorted(missing))

    if unknown:
        print("WARNING: Preview contains employees not found as active:")
        print(sorted(unknown))

    # ==========================================
    # STEP 6: FINAL VALIDATION SUMMARY
    # ==========================================

    has_errors = (
        not duplicates.empty
        or len(capacity_violations) > 0
        or not invalid_unavailable.empty
        or len(missing) > 0
        or len(unknown) > 0
    )

    print("\n========== FINAL VALIDATION SUMMARY ==========")

    print("Duplicate employee records:", len(duplicates))
    print("Capacity violations:", len(capacity_violations))
    print("Unavailable employees incorrectly allocated:",
          len(invalid_unavailable))
    print("Active employees missing:", len(missing))
    print("Unknown or inactive employees:", len(unknown))

    if has_errors:
        print("\nDAILY ALLOCATION VALIDATION FAILED.")
        print("Please review the reported issues.")
    else:
        print("\nDAILY ALLOCATION VALIDATION PASSED.")

    print("\nEmployee and station master data came from PostgreSQL.")
    print("No PostgreSQL records were modified.")

    print("\n========== VALIDATION COMPLETED ==========")


if __name__ == "__main__":
    validate_daily_allocations()
