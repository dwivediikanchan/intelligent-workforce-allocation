import pandas as pd

from database_repository import (
    get_employees,
    get_employee_skills
)


def generate_skill_analysis():

    # ==========================================
    # STEP 1: LOAD DATA FROM POSTGRESQL
    # ==========================================

    employees = get_employees()
    skills = get_employee_skills()

    print("\n========== EMPLOYEE SKILL ANALYSIS ==========")

    print("Employee details: PostgreSQL")
    print("Employee skills: PostgreSQL")

    if employees.empty:
        print("No employee records found.")
        return

    # ==========================================
    # STEP 2: USE VERIFIED SKILLS ONLY
    # ==========================================

    verified_skills = skills[
        skills["verification_status"]
        .astype(str)
        .str.strip()
        .str.lower() == "verified"
    ].copy()

    print("\nTotal employees:", len(employees))
    print("Total skill records:", len(skills))
    print("Verified skill records:", len(verified_skills))

    # ==========================================
    # STEP 3: COUNT VERIFIED SKILLS
    # ==========================================

    skill_count = (
        verified_skills.groupby("employee_id")["skill_name"]
        .nunique()
        .reset_index(name="total_verified_skills")
    )

    # ==========================================
    # STEP 4: CALCULATE PROFICIENCY METRICS
    # ==========================================

    skill_metrics = (
        verified_skills.groupby("employee_id")["proficiency_level"]
        .agg(
            average_proficiency="mean",
            highest_proficiency="max"
        )
        .reset_index()
    )

    # ==========================================
    # STEP 5: COMBINE EMPLOYEE INFORMATION
    # ==========================================

    employee_analysis = (
        employees
        .merge(skill_count, on="employee_id", how="left")
        .merge(skill_metrics, on="employee_id", how="left")
    )

    employee_analysis["total_verified_skills"] = (
        employee_analysis["total_verified_skills"]
        .fillna(0)
        .astype(int)
    )

    # ==========================================
    # STEP 6: CLASSIFY EMPLOYEES
    # ==========================================

    employee_analysis["employee_category"] = "Specialist"

    employee_analysis.loc[
        (
            employee_analysis["total_verified_skills"] >= 3
        )
        & (
            employee_analysis["average_proficiency"] >= 3
        ),
        "employee_category"
    ] = "Potential All-Rounder"

    employee_analysis.loc[
        employee_analysis["total_verified_skills"] == 0,
        "employee_category"
    ] = "No Verified Skills"

    # ==========================================
    # STEP 7: DISPLAY EMPLOYEE SKILL PROFILES
    # ==========================================

    print("\n--- EMPLOYEE SKILL PROFILE ---")

    print(
        employee_analysis.round(2).to_string(index=False)
    )

    # ==========================================
    # STEP 8: VERIFIED SKILL DISTRIBUTION
    # ==========================================

    print("\n--- VERIFIED SKILL DISTRIBUTION ---")

    if verified_skills.empty:
        print("No verified skills available.")
    else:
        print(
            verified_skills["skill_name"].value_counts()
        )

    # ==========================================
    # STEP 9: EMPLOYEE CATEGORY DISTRIBUTION
    # ==========================================

    print("\n--- EMPLOYEE CATEGORIES ---")

    print(
        employee_analysis["employee_category"].value_counts()
    )

    # ==========================================
    # STEP 10: EMPLOYEES WITHOUT VERIFIED SKILLS
    # ==========================================

    print("\n--- EMPLOYEES WITHOUT VERIFIED SKILLS ---")

    employees_without_skills = employee_analysis[
        employee_analysis["total_verified_skills"] == 0
    ][["employee_id", "employee_name"]]

    if employees_without_skills.empty:
        print("All employees have at least one verified skill.")
    else:
        print(employees_without_skills.to_string(index=False))

    print("\nEmployee details and skills: PostgreSQL")
    print("No PostgreSQL records were modified.")

    print("\n========== ANALYSIS COMPLETED ==========")


if __name__ == "__main__":
    generate_skill_analysis()