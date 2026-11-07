import pandas as pd

from database_repository import (
    get_employees,
    get_employee_skills,
    get_stations
)


def run_data_quality_checks():

    # ==========================================
    # STEP 1: LOAD DATA FROM POSTGRESQL
    # ==========================================

    employees = get_employees()
    employee_skills = get_employee_skills()
    stations = get_stations()

    print("\n========== DATA QUALITY REPORT ==========")

    print("Employees: PostgreSQL")
    print("Employee skills: PostgreSQL")
    print("Stations: PostgreSQL")

    if employees.empty or employee_skills.empty or stations.empty:
        print("\nWARNING: One or more datasets are empty.")

    results = {}

    # ==========================================
    # STEP 2: MISSING VALUES
    # ==========================================

    print("\n1. MISSING VALUES")

    for name, dataset in [
        ("Employees", employees),
        ("Employee Skills", employee_skills),
        ("Stations", stations)
    ]:
        missing = dataset.isnull().sum()

        print(f"\n{name}:")
        print(missing)

        results[f"{name} missing values"] = int(
            missing.sum()
        ) == 0

    # ==========================================
    # STEP 3: DUPLICATE EMPLOYEE IDS
    # ==========================================

    print("\n2. DUPLICATE EMPLOYEES")

    duplicate_employees = employees[
        employees.duplicated(
            subset=["employee_id"],
            keep=False
        )
    ]

    print(duplicate_employees.to_string(index=False))

    results["Duplicate employees"] = duplicate_employees.empty

    # ==========================================
    # STEP 4: DUPLICATE EMPLOYEE-SKILL RECORDS
    # ==========================================

    print("\n3. DUPLICATE SKILL RECORDS")

    duplicate_skills = employee_skills[
        employee_skills.duplicated(
            subset=["employee_id", "skill_name"],
            keep=False
        )
    ]

    print(duplicate_skills.to_string(index=False))

    results["Duplicate skill records"] = duplicate_skills.empty

    # ==========================================
    # STEP 5: INVALID PROFICIENCY LEVELS
    # ==========================================

    print("\n4. INVALID SKILL LEVELS")

    proficiency = pd.to_numeric(
        employee_skills["proficiency_level"],
        errors="coerce"
    )

    invalid_skills = employee_skills[
        proficiency.isna()
        | ~proficiency.between(1, 5)
    ]

    print(invalid_skills.to_string(index=False))

    results["Invalid proficiency levels"] = invalid_skills.empty

    # ==========================================
    # STEP 6: UNKNOWN EMPLOYEE IDS
    # ==========================================

    print("\n5. UNKNOWN EMPLOYEE IDS")

    unknown_employees = employee_skills[
        ~employee_skills["employee_id"].isin(
            employees["employee_id"]
        )
    ]

    print(unknown_employees.to_string(index=False))

    results["Unknown employee IDs"] = unknown_employees.empty

    # ==========================================
    # STEP 7: INVALID STATION CAPACITY
    # ==========================================

    print("\n6. INVALID STATION CAPACITY")

    capacity = pd.to_numeric(
        stations["capacity"],
        errors="coerce"
    )

    invalid_capacity = stations[
        capacity.isna() | (capacity <= 0)
    ]

    print(invalid_capacity.to_string(index=False))

    results["Invalid station capacity"] = invalid_capacity.empty

    # ==========================================
    # STEP 8: FINAL QUALITY SUMMARY
    # ==========================================

    print("\n--- DATA QUALITY SUMMARY ---")

    for check, passed in results.items():
        print(f"{check}: {'PASS' if passed else 'FAIL'}")

    total_checks = len(results)
    passed_checks = sum(results.values())

    print(f"\nChecks passed: {passed_checks}/{total_checks}")

    print("\nData source: PostgreSQL")
    print("No PostgreSQL records were modified.")

    if passed_checks == total_checks:
        print("\nOVERALL RESULT: PASS")
    else:
        print("\nOVERALL RESULT: REVIEW REQUIRED")

    print("\n========== QUALITY CHECK COMPLETED ==========")


if __name__ == "__main__":
    run_data_quality_checks()