import pandas as pd

from database_repository import (
    get_employees,
    get_employee_skills,
    get_stations
)


def inspect_workforce_data():

    # ==========================================
    # STEP 1: LOAD DATA FROM POSTGRESQL
    # ==========================================

    employees = get_employees()
    employee_skills = get_employee_skills()
    stations = get_stations()

    print("\n========== WORKFORCE DATA INSPECTION ==========")

    print("Employees: PostgreSQL")
    print("Employee skills: PostgreSQL")
    print("Stations: PostgreSQL")

    # ==========================================
    # STEP 2: DISPLAY EMPLOYEE INFORMATION
    # ==========================================

    print("\n--- EMPLOYEE DATA ---")

    if employees.empty:
        print("No employee records found.")
    else:
        print(employees.head().to_string(index=False))

    # ==========================================
    # STEP 3: DISPLAY EMPLOYEE SKILLS
    # ==========================================

    print("\n--- EMPLOYEE SKILLS ---")

    if employee_skills.empty:
        print("No employee skill records found.")
    else:
        print(employee_skills.head().to_string(index=False))

    # ==========================================
    # STEP 4: DISPLAY STATION INFORMATION
    # ==========================================

    print("\n--- STATION DATA ---")

    if stations.empty:
        print("No station records found.")
    else:
        print(stations.head().to_string(index=False))

    # ==========================================
    # STEP 5: DATASET DIMENSIONS
    # ==========================================

    print("\n--- DATASET SHAPES ---")

    print("Employees:", employees.shape)
    print("Employee Skills:", employee_skills.shape)
    print("Stations:", stations.shape)

    print("\nAll datasets loaded from PostgreSQL.")
    print("No PostgreSQL records were modified.")

    print("\n========== DATA INSPECTION COMPLETED ==========")


if __name__ == "__main__":
    inspect_workforce_data()