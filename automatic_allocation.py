
import pandas as pd

from database_repository import (
    get_employees,
    get_employee_skills,
    get_stations,
    get_station_requirements
)


def run_automatic_allocation():

    # -------------------------------------------------
    # STEP 1: LOAD DATA FROM POSTGRESQL
    # -------------------------------------------------

    print("\n========== LOADING POSTGRESQL DATA ==========")

    employees = get_employees()
    employee_skills = get_employee_skills()
    stations = get_stations()
    requirements = get_station_requirements()

    if employees.empty or stations.empty or requirements.empty:
        print("ERROR: Required employee, station or requirement data is missing.")
        return

    # -------------------------------------------------
    # STEP 2: FILTER ACTIVE EMPLOYEES
    # -------------------------------------------------

    employees = employees[
        employees["status"].astype(str).str.lower() == "active"
    ].copy()

    # Use only verified employee skills
    employee_skills = employee_skills[
        employee_skills["verification_status"].astype(str).str.lower()
        == "verified"
    ].copy()

    print("Active employees:", len(employees))
    print("Verified skill records:", len(employee_skills))
    print("Stations:", len(stations))

    # -------------------------------------------------
    # STEP 3: BUILD VERIFIED SKILL MAP
    # -------------------------------------------------

    skill_map = {
        emp_id: dict(
            zip(group["skill_name"], group["proficiency_level"])
        )
        for emp_id, group in employee_skills.groupby("employee_id")
    }

    station_capacity = dict(
        zip(stations["station_id"], stations["capacity"])
    )

    # -------------------------------------------------
    # STEP 4: PREPARE ALLOCATION TRACKING
    # -------------------------------------------------

    station_counts = {}

    allocations = []
    employee_candidates = {}

    print("\n========== VERIFIED SKILL AUTOMATIC ALLOCATION ==========")

    # -------------------------------------------------
    # STEP 5: FIND ELIGIBLE STATIONS
    # -------------------------------------------------

    for _, employee in employees.iterrows():

        emp_id = employee["employee_id"]
        emp_skills = skill_map.get(emp_id, {})

        candidates = []

        for station_id in stations["station_id"]:

            rules = requirements[
                requirements["station_id"] == station_id
            ]

            eligible = True
            score = 0

            for _, rule in rules.iterrows():

                skill = rule["skill_name"]
                minimum = rule["min_proficiency"]
                weight = rule["weight"]

                mandatory_value = str(rule["mandatory"]).lower()
                mandatory = mandatory_value in ["true", "1", "yes"]

                level = emp_skills.get(skill, 0)

                if pd.isna(level):
                    level = 0

                # Mandatory verified skill check
                if mandatory and level < minimum:
                    eligible = False
                    break

                # Weighted skill score
                score += (level / 5) * weight * 100

            if eligible:
                candidates.append({
                    "station_id": station_id,
                    "skill_score": round(score, 2)
                })

        employee_candidates[emp_id] = candidates

    # -------------------------------------------------
    # STEP 6: PRIORITIZE EMPLOYEES WITH FEWER OPTIONS
    # -------------------------------------------------

    employee_order = sorted(
        employees.to_dict("records"),
        key=lambda emp: len(
            employee_candidates[emp["employee_id"]]
        )
    )

    # -------------------------------------------------
    # STEP 7: ALLOCATE EMPLOYEES
    # -------------------------------------------------

    for employee in employee_order:

        emp_id = employee["employee_id"]
        emp_name = employee["employee_name"]
        shift = employee["shift"]

        candidates = employee_candidates[emp_id]

        available_candidates = []

        for candidate in candidates:

            station_id = candidate["station_id"]
            key = (station_id, shift)

            if key not in station_counts:
                station_counts[key] = 0

            capacity = station_capacity[station_id]

            if pd.isna(capacity) or capacity <= 0:
                continue

            assigned = station_counts[key]

            if assigned < capacity:

                utilization = assigned / capacity

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

            allocations.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "station_id": station_id,
                "shift": shift,
                "skill_score": selected["skill_score"],
                "status": "Allocated"
            })

        else:

            allocations.append({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "station_id": "Not Assigned",
                "shift": shift,
                "skill_score": 0,
                "status": "Unallocated"
            })

    # -------------------------------------------------
    # STEP 8: DISPLAY ALLOCATIONS
    # -------------------------------------------------

    allocation_df = pd.DataFrame(allocations)

    print("\n--- FINAL EMPLOYEE ALLOCATIONS ---")

    if allocation_df.empty:
        print("No employees available for allocation.")
    else:
        print(allocation_df.to_string(index=False))

    # -------------------------------------------------
    # STEP 9: STATION UTILIZATION BY SHIFT
    # -------------------------------------------------

    print("\n--- STATION UTILIZATION BY SHIFT ---")

    utilization_rows = []

    for _, station in stations.iterrows():

        station_id = station["station_id"]
        capacity = station["capacity"]

        for shift in employees["shift"].dropna().unique():

            assigned = station_counts.get(
                (station_id, shift), 0
            )

            available_capacity = max(
                capacity - assigned, 0
            ) if pd.notna(capacity) else 0

            utilization_percentage = (
                round(assigned / capacity * 100, 2)
                if pd.notna(capacity) and capacity > 0
                else 0
            )

            utilization_rows.append({
                "station_id": station_id,
                "station_name": station["station_name"],
                "shift": shift,
                "capacity": capacity,
                "assigned_employees": assigned,
                "available_capacity": available_capacity,
                "utilization_percentage": utilization_percentage
            })

    utilization_report = pd.DataFrame(utilization_rows)

    if utilization_report.empty:
        print("No utilization records available.")
    else:
        print(utilization_report.to_string(index=False))

    # -------------------------------------------------
    # STEP 10: EXPORT PREVIEW
    # -------------------------------------------------

    allocation_df.to_csv(
        "data/automatic_allocations.csv",
        index=False
    )

    print("\nAllocation preview saved to data/automatic_allocations.csv")

    print("\nPostgreSQL master data was read successfully.")
    print("No PostgreSQL allocation records were modified.")

    print("\n========== AUTOMATIC ALLOCATION COMPLETED ==========")


if __name__ == "__main__":
    run_automatic_allocation()
