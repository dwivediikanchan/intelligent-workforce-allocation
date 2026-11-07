
import pandas as pd

from database_repository import get_employees


def check_employee_coverage():

    # ==========================================
    # STEP 1: LOAD DATA
    # ==========================================

    print("\n========== LOADING VALIDATION DATA ==========")

    employees = get_employees()

    allocations = pd.read_csv(
        "data/automatic_allocations.csv"
    )

    if employees.empty:
        print("ERROR: No employee records found in PostgreSQL.")
        return

    if allocations.empty:
        print("ERROR: Automatic allocation preview is empty.")
        return

    print("Employee master data: PostgreSQL")
    print("Automatic allocation preview: CSV")

    # ==========================================
    # STEP 2: ACTIVE EMPLOYEE COVERAGE
    # ==========================================

    active_employees = employees[
        employees["status"].astype(str).str.lower() == "active"
    ]

    allocated_employee_ids = set(
        allocations["employee_id"].dropna()
    )

    missing_employees = active_employees[
        ~active_employees["employee_id"].isin(
            allocated_employee_ids
        )
    ]

    # ==========================================
    # STEP 3: UNKNOWN EMPLOYEE CHECK
    # ==========================================

    active_employee_ids = set(
        active_employees["employee_id"]
    )

    unknown_employee_ids = (
        allocated_employee_ids - active_employee_ids
    )

    print("\n========== EMPLOYEE COVERAGE VALIDATION ==========")

    if missing_employees.empty:
        print("PASS: All active employees are accounted for.")
    else:
        print("FAIL: Some active employees are missing.")
        print(
            missing_employees[
                ["employee_id", "employee_name"]
            ].to_string(index=False)
        )

    if unknown_employee_ids:
        print("\nWARNING: Unknown or inactive employees in preview:")
        print(sorted(unknown_employee_ids))
    else:
        print("PASS: No unknown or inactive employees in preview.")

    # ==========================================
    # STEP 4: SUMMARY
    # ==========================================

    print("\nTotal active employees:", len(active_employees))
    print("Total allocation records:", len(allocations))
    print("Missing active employees:", len(missing_employees))
    print("Unknown or inactive employees:", len(unknown_employee_ids))

    print("\nEmployee master data was read from PostgreSQL.")
    print("No PostgreSQL records were modified.")

    print("\n========== COVERAGE CHECK COMPLETED ==========")


if __name__ == "__main__":
    check_employee_coverage()
