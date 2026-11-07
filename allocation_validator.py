
import pandas as pd

from database_repository import (
    get_employee_skills,
    get_stations,
    get_station_requirements,
    get_allocations
)


# =====================================================
# 1. EXISTING POSTGRESQL ALLOCATION VALIDATOR
# =====================================================

def validate_allocations():

    print("\n========== LOADING POSTGRESQL DATA ==========")

    employee_skills = get_employee_skills()
    stations = get_stations()
    requirements = get_station_requirements()
    assignments = get_allocations()

    print("\n========== UNIFIED ALLOCATION VALIDATION ==========")

    if assignments.empty:
        print("No allocation records found in PostgreSQL.")
        return

    required_assignment_columns = [
        "employee_id", "station_id", "shift",
        "allocation_date", "status"
    ]

    required_skill_columns = [
        "employee_id", "skill_name",
        "proficiency_level", "verification_status"
    ]

    required_station_columns = [
        "station_id", "capacity"
    ]

    required_rule_columns = [
        "station_id", "skill_name",
        "min_proficiency", "mandatory"
    ]

    datasets = [
        (assignments, required_assignment_columns, "Assignments"),
        (employee_skills, required_skill_columns, "Employee skills"),
        (stations, required_station_columns, "Stations"),
        (requirements, required_rule_columns, "Station requirements")
    ]

    for dataframe, columns, name in datasets:

        missing = [
            column for column in columns
            if column not in dataframe.columns
        ]

        if missing:
            print(f"ERROR: {name} missing columns: {missing}")
            return

    assignments = assignments[
        assignments["status"].astype(str).str.strip() == "Allocated"
    ].copy()

    # CHECK 1: DUPLICATE ASSIGNMENTS

    print("\n--- CHECK 1: DUPLICATE ASSIGNMENTS ---")

    duplicate_keys = [
        "employee_id",
        "station_id",
        "allocation_date",
        "shift"
    ]

    duplicates = assignments[
        assignments.duplicated(
            subset=duplicate_keys,
            keep=False
        )
    ]

    if duplicates.empty:
        print("PASS: No duplicate assignments.")
    else:
        print("FAIL: Duplicate assignments found.")
        print(duplicates.to_string(index=False))

    # CHECK 2: MULTIPLE STATION ASSIGNMENTS

    print("\n--- CHECK 2: MULTIPLE STATION ASSIGNMENTS ---")

    multiple = (
        assignments.groupby(
            ["employee_id", "allocation_date", "shift"]
        )["station_id"]
        .nunique()
        .reset_index(name="station_count")
    )

    conflicts = multiple[
        multiple["station_count"] > 1
    ]

    if conflicts.empty:
        print("PASS: No employee assigned to multiple stations.")
    else:
        print("FAIL: Multiple station assignments found.")
        print(conflicts.to_string(index=False))

    # CHECK 3: STATION CAPACITY

    print("\n--- CHECK 3: STATION CAPACITY ---")

    capacity_report = assignments.merge(
        stations[["station_id", "capacity"]],
        on="station_id",
        how="left"
    )

    capacity_report = (
        capacity_report.groupby(
            [
                "station_id",
                "allocation_date",
                "shift",
                "capacity"
            ],
            dropna=False
        )
        .size()
        .reset_index(name="assigned_employees")
    )

    capacity_report["status"] = capacity_report.apply(
        lambda row: (
            "Unknown Capacity"
            if pd.isna(row["capacity"])
            else (
                "Over Capacity"
                if row["assigned_employees"] > row["capacity"]
                else "Within Capacity"
            )
        ),
        axis=1
    )

    if capacity_report.empty:
        print("No allocated records available for capacity validation.")
    else:
        print(capacity_report.to_string(index=False))

    # CHECK 4: VERIFIED SKILL ELIGIBILITY

    print("\n--- CHECK 4: VERIFIED SKILL ELIGIBILITY ---")

    verified_skills = employee_skills[
        employee_skills["verification_status"]
        .astype(str).str.strip().str.lower() == "verified"
    ].copy()

    skill_map = {
        emp_id: dict(
            zip(
                group["skill_name"],
                group["proficiency_level"]
            )
        )
        for emp_id, group in verified_skills.groupby("employee_id")
    }

    mandatory_rules = requirements[
        requirements["mandatory"].astype(str)
        .str.strip().str.lower()
        .isin(["true", "1", "yes"])
    ]

    eligibility_results = []

    for _, assignment in assignments.iterrows():

        emp_id = assignment["employee_id"]
        station_id = assignment["station_id"]

        station_rules = mandatory_rules[
            mandatory_rules["station_id"] == station_id
        ]

        employee_skill_map = skill_map.get(emp_id, {})

        missing_skills = []

        for _, rule in station_rules.iterrows():

            skill = rule["skill_name"]
            minimum = rule["min_proficiency"]

            actual_level = employee_skill_map.get(skill, 0)

            if pd.isna(actual_level) or actual_level < minimum:
                missing_skills.append(skill)

        if station_rules.empty:
            status = "No Mandatory Rules"
            reason = "No mandatory requirements configured"

        elif missing_skills:
            status = "Not Eligible"
            reason = ", ".join(missing_skills)

        else:
            status = "Eligible"
            reason = "All verified mandatory skills satisfied"

        eligibility_results.append({
            "employee_id": emp_id,
            "station_id": station_id,
            "allocation_date": assignment["allocation_date"],
            "shift": assignment["shift"],
            "status": status,
            "reason": reason
        })

    eligibility_report = pd.DataFrame(eligibility_results)

    if eligibility_report.empty:
        print("No assignments available for skill validation.")
    else:
        print(eligibility_report.to_string(index=False))

    # CHECK 5: EMPLOYEE SHIFT ASSIGNMENTS

    print("\n--- CHECK 5: EMPLOYEE SHIFT ASSIGNMENTS ---")

    shift_report = (
        assignments.groupby("employee_id")["shift"]
        .nunique()
        .reset_index(name="number_of_shifts")
    )

    if shift_report.empty:
        print("No employee shift assignments found.")
    else:
        print(shift_report.to_string(index=False))

    # FINAL SUMMARY

    capacity_violations = capacity_report[
        capacity_report["status"].isin(
            ["Over Capacity", "Unknown Capacity"]
        )
    ]

    skill_violations = eligibility_report[
        eligibility_report["status"] == "Not Eligible"
    ]

    has_errors = (
        not duplicates.empty
        or not conflicts.empty
        or not capacity_violations.empty
        or not skill_violations.empty
    )

    print("\n========== FINAL VALIDATION SUMMARY ==========")

    print("Allocated records checked:", len(assignments))
    print("Duplicate assignments:", len(duplicates))
    print("Multiple station conflicts:", len(conflicts))
    print("Capacity violations:", len(capacity_violations))
    print("Skill eligibility violations:", len(skill_violations))

    if has_errors:
        print("\nALLOCATION VALIDATION FAILED.")
    else:
        print("\nALLOCATION VALIDATION PASSED.")

    print("\nMaster data was read from PostgreSQL.")
    print("No PostgreSQL records were modified.")
    print("\n========== PROCESS COMPLETED ==========")


# =====================================================
# 2. NEW SMART ALLOCATION PREVIEW VALIDATOR
# =====================================================

def validate_allocation_preview(preview, allocation_date=None):

    print("\n========== PREVIEW ALLOCATION VALIDATION ==========")

    required_columns = [
        "employee_id",
        "station_id",
        "shift",
        "status"
    ]

    missing = [
        column for column in required_columns
        if column not in preview.columns
    ]

    if missing:
        return {
            "passed": False,
            "errors": [f"Missing preview columns: {missing}"]
        }

    if preview.empty:
        return {
            "passed": False,
            "errors": ["Allocation preview is empty."]
        }

    # Load PostgreSQL master data

    employee_skills = get_employee_skills()
    stations = get_stations()
    requirements = get_station_requirements()

    # Validate master data columns

    required_skill_columns = [
        "employee_id",
        "skill_name",
        "proficiency_level",
        "verification_status"
    ]

    required_station_columns = [
        "station_id",
        "capacity"
    ]

    required_rule_columns = [
        "station_id",
        "skill_name",
        "min_proficiency",
        "mandatory"
    ]

    datasets = [
        (employee_skills, required_skill_columns, "Employee skills"),
        (stations, required_station_columns, "Stations"),
        (requirements, required_rule_columns, "Station requirements")
    ]

    errors = []

    for dataframe, columns, name in datasets:

        missing_columns = [
            column for column in columns
            if column not in dataframe.columns
        ]

        if missing_columns:
            errors.append(
                f"{name} missing columns: {missing_columns}"
            )

    if errors:
        return {
            "passed": False,
            "errors": errors
        }

    # Validate only allocated employees

    assignments = preview[
        preview["status"].astype(str).str.strip().str.lower()
        == "allocated"
    ].copy()

    if assignments.empty:
        return {
            "passed": False,
            "errors": ["No allocated employees found in preview."]
        }

    # Normalize identifiers and text

    for dataframe, columns in [
        (
            assignments,
            ["employee_id", "station_id", "shift"]
        ),
        (
            employee_skills,
            ["employee_id", "skill_name", "verification_status"]
        ),
        (
            stations,
            ["station_id"]
        ),
        (
            requirements,
            ["station_id", "skill_name"]
        )
    ]:

        for column in columns:
            dataframe[column] = (
                dataframe[column].astype(str).str.strip()
            )

    assignments["shift"] = assignments["shift"].str.lower()

    # CHECK 1: DUPLICATE ASSIGNMENTS

    print("\n--- CHECK 1: DUPLICATE ASSIGNMENTS ---")

    duplicates = assignments[
        assignments.duplicated(
            subset=["employee_id", "station_id", "shift"],
            keep=False
        )
    ]

    if not duplicates.empty:
        errors.append("Duplicate assignments found.")

    # CHECK 2: MULTIPLE STATION ASSIGNMENTS

    print("\n--- CHECK 2: MULTIPLE STATION ASSIGNMENTS ---")

    multiple = (
        assignments.groupby(
            ["employee_id", "shift"]
        )["station_id"]
        .nunique()
    )

    conflicts = multiple[multiple > 1]

    if not conflicts.empty:
        errors.append(
            "Employees assigned to multiple stations in the same shift."
        )

    # CHECK 3: STATION CAPACITY

    print("\n--- CHECK 3: STATION CAPACITY ---")

    capacity_data = assignments.merge(
        stations[["station_id", "capacity"]],
        on="station_id",
        how="left"
    )

    capacity_data["capacity"] = pd.to_numeric(
        capacity_data["capacity"],
        errors="coerce"
    )

    capacity_report = (
        capacity_data.groupby(
            ["station_id", "shift", "capacity"],
            dropna=False
        )
        .size()
        .reset_index(name="assigned_employees")
    )

    capacity_violations = capacity_report[
        capacity_report["capacity"].isna()
        | (
            capacity_report["assigned_employees"]
            > capacity_report["capacity"]
        )
    ]

    if not capacity_violations.empty:
        errors.append(
            "Station capacity violations or unknown station capacities found."
        )

    # CHECK 4: MANDATORY VERIFIED SKILLS

    print("\n--- CHECK 4: VERIFIED SKILL ELIGIBILITY ---")

    verified = employee_skills[
        employee_skills["verification_status"].str.lower()
        == "verified"
    ].copy()

    verified["proficiency_level"] = pd.to_numeric(
        verified["proficiency_level"],
        errors="coerce"
    )

    skill_map = {}

    for _, row in verified.iterrows():

        key = (
            row["employee_id"],
            row["skill_name"].casefold()
        )

        level = row["proficiency_level"]

        if pd.isna(level):
            level = 0

        skill_map[key] = max(
            skill_map.get(key, 0),
            level
        )

    mandatory = requirements[
        requirements["mandatory"].astype(str)
        .str.strip().str.lower()
        .isin(["true", "1", "yes"])
    ].copy()

    mandatory["min_proficiency"] = pd.to_numeric(
        mandatory["min_proficiency"],
        errors="coerce"
    )

    skill_results = []

    for _, assignment in assignments.iterrows():

        employee_id = assignment["employee_id"]
        station_id = assignment["station_id"]

        station_rules = mandatory[
            mandatory["station_id"] == station_id
        ]

        missing_skills = []

        for _, rule in station_rules.iterrows():

            skill_key = (
                employee_id,
                rule["skill_name"].casefold()
            )

            actual_level = skill_map.get(skill_key, 0)
            minimum = rule["min_proficiency"]

            if pd.isna(minimum) or actual_level < minimum:
                missing_skills.append(rule["skill_name"])

        skill_results.append({
            "employee_id": employee_id,
            "station_id": station_id,
            "status": (
                "Not Eligible"
                if missing_skills
                else "Eligible"
            ),
            "missing_skills": ", ".join(missing_skills)
        })

    skill_report = pd.DataFrame(skill_results)

    skill_violations = skill_report[
        skill_report["status"] == "Not Eligible"
    ]

    if not skill_violations.empty:
        errors.append(
            "Mandatory verified skill eligibility violations found."
        )

    # FINAL VALIDATION SUMMARY

    passed = len(errors) == 0

    print("\n========== PREVIEW VALIDATION SUMMARY ==========")

    print("Allocation date:", allocation_date)
    print("Allocated employees:", len(assignments))
    print("Duplicate assignments:", len(duplicates))
    print("Multiple station conflicts:", len(conflicts))
    print("Capacity violations:", len(capacity_violations))
    print("Skill eligibility violations:", len(skill_violations))

    print("\nCapacity report:")
    print(capacity_report.to_string(index=False))

    print("\nSkill eligibility report:")
    print(skill_report.to_string(index=False))

    if passed:
        print("\nPREVIEW VALIDATION PASSED.")
    else:
        print("\nPREVIEW VALIDATION FAILED.")

        for error in errors:
            print("-", error)

    print("\nPostgreSQL records were not modified.")

    return {
        "passed": passed,
        "errors": errors,
        "duplicate_report": duplicates,
        "conflict_report": conflicts,
        "capacity_report": capacity_report,
        "skill_report": skill_report,
        "summary": {
            "allocated": len(assignments),
            "duplicates": len(duplicates),
            "conflicts": len(conflicts),
            "capacity_violations": len(capacity_violations),
            "skill_violations": len(skill_violations)
        }
    }


# =====================================================
# 3. RUN EXISTING POSTGRESQL VALIDATOR
# =====================================================

if __name__ == "__main__":
    validate_allocations()
