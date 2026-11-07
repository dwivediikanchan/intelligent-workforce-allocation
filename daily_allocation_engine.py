
import pandas as pd
from pathlib import Path

from database_repository import (
    get_employees,
    get_attendance,
    get_employee_skills,
    get_stations,
    get_station_requirements,
    get_allocations
)


# =====================================================
# CONFIGURATION
# =====================================================

DEFAULT_DATE = "2026-11-04"
OUTPUT_FILE = Path("data/daily_allocations.csv")

SHIFTS = ["Morning", "Evening", "Night"]


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def is_true(value):
    return str(value).strip().lower() in [
        "true", "1", "yes", "y"
    ]


# =====================================================
# DAILY ALLOCATION ENGINE
# =====================================================

def run_daily_allocation(selected_date=DEFAULT_DATE):

    selected_date = pd.Timestamp(
        selected_date
    ).strftime("%Y-%m-%d")

    print("\n========== LOADING POSTGRESQL DATA ==========")

    # -------------------------------------------------
    # STEP 1: LOAD DATABASE TABLES
    # -------------------------------------------------

    employees = get_employees()
    attendance = get_attendance()
    employee_skills = get_employee_skills()
    stations = get_stations()
    requirements = get_station_requirements()
    current_allocations = get_allocations()

    required_columns = {
        "employees": [
            "employee_id", "employee_name", "shift", "status"
        ],
        "attendance": [
            "employee_id", "attendance_date",
            "shift", "attendance_status"
        ],
        "employee_skills": [
            "employee_id", "skill_name",
            "proficiency_level", "verification_status"
        ],
        "stations": [
            "station_id", "station_name", "capacity"
        ],
        "requirements": [
            "station_id", "skill_name",
            "min_proficiency", "weight", "mandatory"
        ]
    }

    datasets = {
        "employees": employees,
        "attendance": attendance,
        "employee_skills": employee_skills,
        "stations": stations,
        "requirements": requirements
    }

    for name, columns in required_columns.items():
        missing = set(columns) - set(datasets[name].columns)

        if missing:
            raise ValueError(
                f"{name} table is missing columns: {missing}"
            )

    # Normalize IDs and text fields.

    for dataframe in [
        employees, attendance, employee_skills,
        stations, requirements
    ]:
        if "employee_id" in dataframe.columns:
            dataframe["employee_id"] = (
                dataframe["employee_id"].astype(str).str.strip()
            )

        if "station_id" in dataframe.columns:
            dataframe["station_id"] = (
                dataframe["station_id"].astype(str).str.strip()
            )

    employees["shift"] = employees["shift"].apply(normalize_text)
    employees["status"] = employees["status"].apply(normalize_text)

    attendance["shift"] = attendance["shift"].apply(normalize_text)
    attendance["attendance_status"] = (
        attendance["attendance_status"].apply(normalize_text)
    )

    employee_skills["skill_name"] = (
        employee_skills["skill_name"].apply(normalize_text)
    )

    requirements["skill_name"] = (
        requirements["skill_name"].apply(normalize_text)
    )

    requirements["min_proficiency"] = pd.to_numeric(
        requirements["min_proficiency"], errors="coerce"
    ).fillna(0)

    requirements["weight"] = pd.to_numeric(
        requirements["weight"], errors="coerce"
    ).fillna(0)

    stations["capacity"] = pd.to_numeric(
        stations["capacity"], errors="coerce"
    )

    if stations["capacity"].isna().any():
        raise ValueError("Invalid station capacity found.")

    if (stations["capacity"] < 0).any():
        raise ValueError("Station capacity cannot be negative.")

    # -------------------------------------------------
    # STEP 2: LOAD EXISTING POSTGRESQL ALLOCATIONS
    # -------------------------------------------------

    allocation_columns = [
        "employee_id",
        "station_id",
        "allocation_date",
        "shift",
        "skill_score",
        "status"
    ]

    if current_allocations.empty:
        current_allocations = pd.DataFrame(
            columns=allocation_columns
        )

    else:
        missing = (
            set(allocation_columns)
            - set(current_allocations.columns)
        )

        if missing:
            raise ValueError(
                f"Allocation table is missing columns: {missing}"
            )

        current_allocations["employee_id"] = (
            current_allocations["employee_id"].astype(str).str.strip()
        )

        current_allocations["station_id"] = (
            current_allocations["station_id"].astype(str).str.strip()
        )

        current_allocations["allocation_date"] = pd.to_datetime(
            current_allocations["allocation_date"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d")

        current_allocations["shift"] = (
            current_allocations["shift"].apply(normalize_text)
        )

        current_allocations["status"] = (
            current_allocations["status"].apply(normalize_text)
        )

        current_allocations = current_allocations[
            (current_allocations["allocation_date"] == selected_date)
            & (current_allocations["status"].str.lower() == "allocated")
        ].copy()

    # -------------------------------------------------
    # STEP 3: FILTER ATTENDANCE
    # -------------------------------------------------

    attendance["attendance_date"] = pd.to_datetime(
        attendance["attendance_date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    daily_attendance = attendance[
        attendance["attendance_date"] == selected_date
    ].copy()

    if daily_attendance.duplicated(
        subset=["employee_id"], keep=False
    ).any():
        raise ValueError(
            "Duplicate attendance records found for the selected date."
        )

    # -------------------------------------------------
    # STEP 4: IDENTIFY PRESENT EMPLOYEES
    # -------------------------------------------------

    active_employees = employees[
        employees["status"].str.lower() == "active"
    ].copy()

    present_attendance = daily_attendance[
        daily_attendance["attendance_status"].str.lower() == "present"
    ][["employee_id", "shift"]].copy()

    available_employees = active_employees.merge(
        present_attendance,
        on="employee_id",
        how="inner",
        suffixes=("_employee", "_attendance"),
        validate="one_to_one"
    )

    # Check that attendance shift matches employee shift.

    available_employees["shift_mismatch"] = (
        available_employees["shift_employee"].str.lower()
        != available_employees["shift_attendance"].str.lower()
    )

    shift_mismatches = available_employees[
        available_employees["shift_mismatch"]
    ].copy()

    available_employees = available_employees[
        ~available_employees["shift_mismatch"]
    ].copy()

    available_employees["shift"] = (
        available_employees["shift_employee"]
    )

    # -------------------------------------------------
    # STEP 5: LOAD VERIFIED SKILLS
    # -------------------------------------------------

    employee_skills["proficiency_level"] = pd.to_numeric(
        employee_skills["proficiency_level"],
        errors="coerce"
    ).fillna(0)

    verified_skills = employee_skills[
        employee_skills["verification_status"].str.lower()
        == "verified"
    ].copy()

    skill_map = {}

    for employee_id, group in verified_skills.groupby("employee_id"):

        skill_map[employee_id] = {
            row["skill_name"].lower(): row["proficiency_level"]
            for _, row in group.iterrows()
        }

    # -------------------------------------------------
    # STEP 6: DISPLAY INPUT DATA
    # -------------------------------------------------

    print("\n========== DAILY ALLOCATION INPUTS ==========")

    print("\n--- Available Employees ---")

    if available_employees.empty:
        print("No eligible present employees found.")
    else:
        print(
            available_employees[
                ["employee_id", "employee_name", "shift"]
            ].to_string(index=False)
        )

    print("\n--- Verified Employee Skills ---")
    print(verified_skills.to_string(index=False))

    print("\n--- Station Requirements ---")
    print(requirements.to_string(index=False))

    print("\nAvailable employee count:", len(available_employees))
    print("Verified skill records:", len(verified_skills))
    print("Station count:", len(stations))

    # -------------------------------------------------
    # STEP 7: IDENTIFY ELIGIBLE STATIONS
    # -------------------------------------------------

    print("\n========== DAILY STATION ELIGIBILITY ==========")

    employee_candidates = {}

    for _, employee in available_employees.iterrows():

        emp_id = employee["employee_id"]
        emp_name = employee["employee_name"]

        emp_skills = skill_map.get(emp_id, {})

        candidates = []

        for _, station in stations.iterrows():

            station_id = station["station_id"]

            rules = requirements[
                requirements["station_id"] == station_id
            ]

            if rules.empty:
                continue

            eligible = True
            total_score = 0.0
            total_weight = rules["weight"].sum()

            for _, rule in rules.iterrows():

                skill = rule["skill_name"].lower()
                minimum = rule["min_proficiency"]
                weight = rule["weight"]

                mandatory = is_true(rule["mandatory"])

                level = emp_skills.get(skill, 0)

                if mandatory and level < minimum:
                    eligible = False
                    break

                total_score += (
                    (level / 5) * weight * 100
                )

            if eligible:

                score = (
                    total_score / total_weight
                    if total_weight > 0
                    else 0
                )

                candidates.append({
                    "station_id": station_id,
                    "skill_score": round(score, 2)
                })

        employee_candidates[emp_id] = candidates

        print(f"\nEmployee: {emp_name} ({emp_id})")

        if candidates:
            for candidate in candidates:
                print(
                    f"Eligible Station: {candidate['station_id']} | "
                    f"Skill Score: {candidate['skill_score']}"
                )
        else:
            print("No eligible station found.")

    # -------------------------------------------------
    # STEP 8: INITIALIZE STATION CAPACITY
    # -------------------------------------------------

    print("\n========== REGENERATING DAILY ALLOCATIONS ==========")

    daily_results = []

    station_counts = {}

    for _, station in stations.iterrows():

        for shift in SHIFTS:

            station_counts[
                (station["station_id"], shift)
            ] = 0

    station_capacity_map = dict(
        zip(stations["station_id"], stations["capacity"])
    )

    processed_employees = set()

    # -------------------------------------------------
    # STEP 9: PRESERVE EXISTING MANAGER ASSIGNMENTS
    # -------------------------------------------------

    for _, employee in available_employees.iterrows():

        emp_id = employee["employee_id"]
        emp_name = employee["employee_name"]
        shift = employee["shift"]

        existing = current_allocations[
            (current_allocations["employee_id"] == emp_id)
            & (current_allocations["shift"] == shift)
        ]

        if existing.empty:
            continue

        if len(existing) > 1:

            daily_results.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "station_id": "Not Assigned",
                "shift": shift,
                "skill_score": 0,
                "status": "Needs Review - Multiple Allocations"
            })

            processed_employees.add(emp_id)
            continue

        old = existing.iloc[0]
        station_id = old["station_id"]

        candidates = employee_candidates.get(emp_id, [])

        candidate = next(
            (
                item for item in candidates
                if item["station_id"] == station_id
            ),
            None
        )

        if candidate is None or station_id not in station_capacity_map:

            daily_results.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "station_id": "Not Assigned",
                "shift": shift,
                "skill_score": 0,
                "status": "Needs Review"
            })

            processed_employees.add(emp_id)
            continue

        station_key = (station_id, shift)

        capacity = station_capacity_map[station_id]

        if station_counts[station_key] < capacity:

            station_counts[station_key] += 1

            daily_results.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "station_id": station_id,
                "shift": shift,
                "skill_score": candidate["skill_score"],
                "status": "Allocated"
            })

        else:

            daily_results.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "station_id": "Not Assigned",
                "shift": shift,
                "skill_score": 0,
                "status": "Needs Review - Capacity Full"
            })

        processed_employees.add(emp_id)

    # -------------------------------------------------
    # STEP 10: ALLOCATE PRESENT UNASSIGNED EMPLOYEES
    # -------------------------------------------------

    for _, employee in available_employees.iterrows():

        emp_id = employee["employee_id"]
        emp_name = employee["employee_name"]
        shift = employee["shift"]

        if emp_id in processed_employees:
            continue

        candidates = employee_candidates.get(emp_id, [])

        available_candidates = []

        for candidate in candidates:

            station_id = candidate["station_id"]
            station_key = (station_id, shift)

            capacity = station_capacity_map[station_id]

            if station_counts[station_key] < capacity:

                utilization = (
                    station_counts[station_key] / capacity
                    if capacity > 0
                    else 1
                )

                available_candidates.append({
                    "station_id": station_id,
                    "skill_score": candidate["skill_score"],
                    "utilization": utilization
                })

        if available_candidates:

            available_candidates.sort(
                key=lambda item: (
                    item["utilization"],
                    -item["skill_score"]
                )
            )

            selected = available_candidates[0]

            station_id = selected["station_id"]

            station_counts[(station_id, shift)] += 1

            daily_results.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "station_id": station_id,
                "shift": shift,
                "skill_score": selected["skill_score"],
                "status": "Allocated"
            })

        elif candidates:

            daily_results.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "station_id": "Not Assigned",
                "shift": shift,
                "skill_score": 0,
                "status": "Station Capacity Full"
            })

        else:

            daily_results.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "station_id": "Not Assigned",
                "shift": shift,
                "skill_score": 0,
                "status": "Present - No Eligible Station"
            })

        processed_employees.add(emp_id)

    # -------------------------------------------------
    # STEP 11: RECORD SHIFT MISMATCHES
    # -------------------------------------------------

    for _, employee in shift_mismatches.iterrows():

        daily_results.append({
            "employee_id": employee["employee_id"],
            "employee_name": employee["employee_name"],
            "station_id": "Not Assigned",
            "shift": employee["shift_employee"],
            "skill_score": 0,
            "status": "Shift Mismatch - Needs Review"
        })

        processed_employees.add(employee["employee_id"])

    # -------------------------------------------------
    # STEP 12: RECORD ABSENT AND LEAVE EMPLOYEES
    # -------------------------------------------------

    all_employees = employees.merge(
        daily_attendance[
            ["employee_id", "attendance_status"]
        ],
        on="employee_id",
        how="left"
    )

    for _, employee in all_employees.iterrows():

        emp_id = employee["employee_id"]

        if emp_id in processed_employees:
            continue

        if emp_id in available_employees["employee_id"].values:
            continue

        attendance_status = employee["attendance_status"]

        if isinstance(attendance_status, str):

            if attendance_status.lower() in ["absent", "leave"]:

                daily_results.append({
                    "employee_id": emp_id,
                    "employee_name": employee["employee_name"],
                    "station_id": "Not Assigned",
                    "shift": employee["shift"],
                    "skill_score": 0,
                    "status": attendance_status.title()
                })

    # -------------------------------------------------
    # STEP 13: CREATE AND VALIDATE PREVIEW
    # -------------------------------------------------

    daily_allocations = pd.DataFrame(
        daily_results,
        columns=[
            "employee_id",
            "employee_name",
            "station_id",
            "shift",
            "skill_score",
            "status"
        ]
    )

    if not daily_allocations.empty:

        allocated = daily_allocations[
            daily_allocations["status"] == "Allocated"
        ]

        # Check duplicate employee allocations.

        duplicates = allocated[
            allocated.duplicated(
                subset=["employee_id", "shift"],
                keep=False
            )
        ]

        if not duplicates.empty:
            raise ValueError(
                "Duplicate employee allocations detected."
            )

        # Check station capacity.

        capacity_check = (
            allocated.groupby(["station_id", "shift"])
            .size()
            .reset_index(name="allocated_count")
        )

        for _, row in capacity_check.iterrows():

            capacity = station_capacity_map[row["station_id"]]

            if row["allocated_count"] > capacity:
                raise ValueError(
                    f"Capacity exceeded at {row['station_id']} "
                    f"for {row['shift']} shift."
                )

    # -------------------------------------------------
    # STEP 14: SAVE PREVIEW CSV
    # -------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    daily_allocations.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n--- UPDATED DAILY ALLOCATIONS ---")

    if daily_allocations.empty:
        print("No daily allocation records generated.")
    else:
        print(
            daily_allocations.to_string(index=False)
        )

    print("\nPreview report saved successfully.")
    print("Master data was read from PostgreSQL.")
    print("Existing manager assignments were preserved.")
    print("PostgreSQL allocation records were NOT modified.")

    return daily_allocations


# =====================================================
# EXECUTION
# =====================================================

if __name__ == "__main__":
    run_daily_allocation()
