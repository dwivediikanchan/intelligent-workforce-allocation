
import pandas as pd

# Load datasets
allocations = pd.read_csv("data/automatic_allocations.csv")
employees = pd.read_csv("data/employees.csv")
stations = pd.read_csv("data/stations.csv")
requirements = pd.read_csv("data/station_requirements.csv")
employee_skills = pd.read_csv("data/employee_skills.csv")

# Only allocated employees
assigned = allocations[
    allocations["status"] == "Allocated"
].copy()

# Only verified skills
verified_skills = employee_skills[
    employee_skills["verification_status"] == "Verified"
]

print("\n========== AUTOMATIC ALLOCATION VALIDATION ==========")

# CHECK 1: Employee coverage
print("\n--- CHECK 1: EMPLOYEE COVERAGE ---")

active_employees = set(
    employees.loc[
        employees["status"] == "Active", "employee_id"
    ]
)

accounted_employees = set(allocations["employee_id"])

missing_employees = active_employees - accounted_employees
unknown_employees = accounted_employees - active_employees

if not missing_employees and not unknown_employees:
    print("PASS: All active employees are accounted for.")
else:
    print("FAIL: Employee coverage issue.")
    print("Missing:", missing_employees)
    print("Unknown:", unknown_employees)


# CHECK 2: Station capacity per shift
print("\n--- CHECK 2: STATION CAPACITY ---")

capacity_report = assigned.merge(
    stations[["station_id", "capacity"]],
    on="station_id",
    how="left"
)

invalid_stations = capacity_report[
    capacity_report["capacity"].isna()
]

capacity_report = capacity_report.dropna(
    subset=["capacity"]
)

capacity_report = (
    capacity_report.groupby(
        ["station_id", "shift", "capacity"]
    )
    .size()
    .reset_index(name="assigned_count")
)

capacity_violations = capacity_report[
    capacity_report["assigned_count"]
    > capacity_report["capacity"]
]

if capacity_violations.empty and invalid_stations.empty:
    print("PASS: No station capacity violations.")
else:
    print("FAIL: Invalid stations or capacity violations.")
    print(invalid_stations.to_string(index=False))
    print(capacity_violations.to_string(index=False))


# CHECK 3: Duplicate assignments
print("\n--- CHECK 3: DUPLICATE ASSIGNMENTS ---")

duplicates = assigned[
    assigned.duplicated(
        subset=["employee_id", "station_id", "shift"],
        keep=False
    )
]

if duplicates.empty:
    print("PASS: No duplicate assignments.")
else:
    print("FAIL: Duplicate assignments found.")
    print(duplicates.to_string(index=False))


# CHECK 4: Employee conflicts
print("\n--- CHECK 4: EMPLOYEE CONFLICTS ---")

employee_counts = (
    assigned.groupby(["employee_id", "shift"])["station_id"]
    .nunique()
)

conflicts = employee_counts[employee_counts > 1]

if conflicts.empty:
    print("PASS: No employee assignment conflicts.")
else:
    print("FAIL: Multiple station assignments found.")
    print(conflicts)


# CHECK 5: Verified mandatory skill eligibility
print("\n--- CHECK 5: VERIFIED SKILL ELIGIBILITY ---")

skill_map = {
    emp_id: dict(
        zip(group["skill_name"], group["proficiency_level"])
    )
    for emp_id, group in verified_skills.groupby("employee_id")
}

skill_violations = []

for _, allocation in assigned.iterrows():

    emp_id = allocation["employee_id"]
    station_id = allocation["station_id"]

    mandatory_rules = requirements[
        (requirements["station_id"] == station_id)
        & (requirements["mandatory"] == True)
    ]

    employee_skill_map = skill_map.get(emp_id, {})

    for _, rule in mandatory_rules.iterrows():

        skill = rule["skill_name"]
        minimum = rule["min_proficiency"]

        actual = employee_skill_map.get(skill, 0)

        if actual < minimum:
            skill_violations.append({
                "employee_id": emp_id,
                "station_id": station_id,
                "skill": skill,
                "required": minimum,
                "verified_level": actual
            })

if not skill_violations:
    print("PASS: All assigned employees meet verified mandatory skills.")
else:
    print("FAIL: Verified skill violations found.")
    print(pd.DataFrame(skill_violations).to_string(index=False))


# FINAL RESULT
print("\n========== FINAL RESULT ==========")

if (
    not missing_employees
    and not unknown_employees
    and capacity_violations.empty
    and invalid_stations.empty
    and duplicates.empty
    and conflicts.empty
    and not skill_violations
):
    print("AUTOMATIC ALLOCATION VALIDATION PASSED.")
else:
    print("AUTOMATIC ALLOCATION VALIDATION FAILED.")

print("\n========== VALIDATION COMPLETED ==========")
