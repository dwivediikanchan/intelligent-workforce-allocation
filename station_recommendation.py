
import pandas as pd

from database_repository import (
    get_employees,
    get_employee_skills,
    get_stations,
    get_station_requirements,
    get_attendance,
    get_allocations
)


def generate_station_recommendations(
    recommendation_date=None
):

    selected_date = (
        str(recommendation_date)
        if recommendation_date
        else "2026-11-04"
    )

    print("\n========== LOADING POSTGRESQL DATA ==========")

    # -------------------------------------------------
    # STEP 1: LOAD DATA FROM POSTGRESQL
    # -------------------------------------------------

    employees = get_employees()
    skills = get_employee_skills()
    stations = get_stations()
    requirements = get_station_requirements()
    attendance = get_attendance()
    allocations = get_allocations()

    required_columns = {
        "employees": [
            "employee_id",
            "employee_name",
            "shift",
            "status"
        ],
        "skills": [
            "employee_id",
            "skill_name",
            "proficiency_level",
            "verification_status"
        ],
        "stations": [
            "station_id",
            "station_name",
            "capacity"
        ],
        "requirements": [
            "station_id",
            "skill_name",
            "min_proficiency",
            "weight",
            "mandatory"
        ],
        "attendance": [
            "employee_id",
            "attendance_date",
            "shift",
            "attendance_status"
        ],
        "allocations": [
            "employee_id",
            "station_id",
            "allocation_date",
            "shift",
            "status"
        ]
    }

    datasets = {
        "employees": employees,
        "skills": skills,
        "stations": stations,
        "requirements": requirements,
        "attendance": attendance,
        "allocations": allocations
    }

    for name, columns in required_columns.items():

        missing = set(columns) - set(datasets[name].columns)

        if missing:
            raise ValueError(
                f"{name} is missing required columns: "
                f"{sorted(missing)}"
            )

    if employees.empty:
        print("No employee records found.")
        return pd.DataFrame(), pd.DataFrame()

    if stations.empty or requirements.empty:
        print("Station or station requirement data is missing.")
        return pd.DataFrame(), pd.DataFrame()

    # -------------------------------------------------
    # STEP 2: NORMALIZE DATES AND DATA TYPES
    # -------------------------------------------------

    attendance = attendance.copy()
    allocations = allocations.copy()

    attendance["attendance_date"] = (
        pd.to_datetime(
            attendance["attendance_date"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    )

    allocations["allocation_date"] = (
        pd.to_datetime(
            allocations["allocation_date"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    )

    allocations["status"] = (
        allocations["status"]
        .astype(str)
        .str.strip()
    )

    employees["status"] = (
        employees["status"]
        .astype(str)
        .str.strip()
    )

    skills["verification_status"] = (
        skills["verification_status"]
        .astype(str)
        .str.strip()
    )

    # -------------------------------------------------
    # STEP 3: FILTER ACTIVE EMPLOYEES
    # -------------------------------------------------

    active_employees = employees[
        employees["status"].str.lower() == "active"
    ].copy()

    # -------------------------------------------------
    # STEP 4: FILTER VERIFIED SKILLS
    # -------------------------------------------------

    verified_skills = skills[
        skills["verification_status"].str.lower()
        == "verified"
    ].copy()

    verified_skills["proficiency_level"] = pd.to_numeric(
        verified_skills["proficiency_level"],
        errors="coerce"
    )

    verified_skills = verified_skills.dropna(
        subset=["proficiency_level"]
    )

    # -------------------------------------------------
    # STEP 5: GET PRESENT EMPLOYEES
    # -------------------------------------------------

    daily_attendance = attendance[
        (attendance["attendance_date"] == selected_date)
        & (
            attendance["attendance_status"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "present"
        )
    ].copy()

    available_employees = active_employees.merge(
        daily_attendance[
            ["employee_id", "shift"]
        ],
        on=["employee_id", "shift"],
        how="inner"
    )

    available_employees = (
        available_employees
        .drop_duplicates(subset=["employee_id", "shift"])
    )

    # -------------------------------------------------
    # STEP 6: FILTER EXISTING ALLOCATIONS
    # -------------------------------------------------

    current_allocations = allocations[
        (allocations["allocation_date"] == selected_date)
        & (allocations["status"].str.lower() == "allocated")
    ].copy()

    # Allocation identity is employee + date + shift.
    # An allocation in another shift must not block
    # a recommendation in the selected shift.

    allocated_keys = set(
        zip(
            current_allocations["employee_id"].astype(str),
            current_allocations["shift"].astype(str)
        )
    )

    # Count current station usage separately by shift.
    allocated_counts = (
        current_allocations
        .groupby(["station_id", "shift"])
        .size()
        .to_dict()
    )

    # -------------------------------------------------
    # STEP 7: BUILD SKILL LOOKUP
    # -------------------------------------------------

    skill_map = {}

    for _, row in verified_skills.iterrows():

        employee_id = str(row["employee_id"])
        skill_name = str(row["skill_name"]).strip().lower()

        skill_map.setdefault(employee_id, {})[
            skill_name
        ] = float(row["proficiency_level"])

    # -------------------------------------------------
    # STEP 8: BUILD STATION REQUIREMENTS
    # -------------------------------------------------

    station_requirements = {}

    for _, row in requirements.iterrows():

        station_id = str(row["station_id"])

        mandatory_value = row["mandatory"]

        if isinstance(mandatory_value, str):
            mandatory_value = (
                mandatory_value.strip().lower()
                in ["true", "1", "yes", "y"]
            )
        else:
            mandatory_value = bool(mandatory_value)

        station_requirements.setdefault(
            station_id, []
        ).append({
            "skill_name": str(
                row["skill_name"]
            ).strip().lower(),

            "min_proficiency": float(
                row["min_proficiency"]
            ),

            "weight": float(row["weight"]),

            "mandatory": mandatory_value
        })

    # -------------------------------------------------
    # STEP 9: STATION CAPACITY LOOKUP
    # -------------------------------------------------

    station_lookup = {}

    for _, row in stations.iterrows():

        station_lookup[str(row["station_id"])] = {
            "station_name": row["station_name"],
            "capacity": int(row["capacity"])
        }

    # -------------------------------------------------
    # STEP 10: GENERATE RECOMMENDATIONS
    # -------------------------------------------------

    recommendations = []
    eligible_results = []

    for _, employee in available_employees.iterrows():

        employee_id = str(employee["employee_id"])
        employee_name = employee["employee_name"]
        employee_shift = str(employee["shift"])

        employee_skills = skill_map.get(
            employee_id, {}
        )

        # ---------------------------------------------
        # ALL-ROUNDER ANALYSIS
        # ---------------------------------------------

        verified_skill_count = len(employee_skills)

        average_proficiency = (
            sum(employee_skills.values())
            / verified_skill_count
            if verified_skill_count > 0
            else 0
        )

        is_all_rounder = (
            verified_skill_count >= 3
            and average_proficiency >= 3
        )

        # ---------------------------------------------
        # EXISTING ALLOCATION CHECK
        # ---------------------------------------------

        already_allocated = (
            employee_id,
            employee_shift
        ) in allocated_keys

        employee_options = []

        # ---------------------------------------------
        # CHECK EVERY STATION
        # ---------------------------------------------

        for station_id, station_data in station_lookup.items():

            station_name = station_data["station_name"]
            capacity = station_data["capacity"]

            station_rules = station_requirements.get(
                station_id, []
            )

            if not station_rules:
                continue

            mandatory_met = True
            total_score = 0.0
            total_weight = 0.0
            missing_skills = []

            # -----------------------------------------
            # MANDATORY SKILL VALIDATION
            # -----------------------------------------

            for rule in station_rules:

                skill_name = rule["skill_name"]
                minimum = rule["min_proficiency"]
                weight = rule["weight"]
                mandatory = rule["mandatory"]

                proficiency = employee_skills.get(
                    skill_name, 0
                )

                if mandatory and proficiency < minimum:

                    mandatory_met = False

                    missing_skills.append(
                        skill_name
                    )

                # Weighted score
                if proficiency >= minimum:

                    normalized_score = min(
                        proficiency / 5 * 100,
                        100
                    )

                else:

                    normalized_score = (
                        proficiency / 5 * 100
                        if proficiency > 0
                        else 0
                    )

                total_score += (
                    normalized_score * weight
                )

                total_weight += weight

            skill_score = (
                round(total_score / total_weight, 2)
                if total_weight > 0
                else 0
            )

            # -----------------------------------------
            # CAPACITY VALIDATION
            # -----------------------------------------

            current_usage = allocated_counts.get(
                (station_id, employee_shift),
                0
            )

            capacity_available = (
                current_usage < capacity
            )

            # -----------------------------------------
            # RECOMMENDATION STATUS
            # -----------------------------------------

            if already_allocated:

                recommendation_status = (
                    "Already Allocated"
                )

            elif not mandatory_met:

                recommendation_status = (
                    "Not Eligible"
                )

            elif not capacity_available:

                recommendation_status = (
                    "Station Full"
                )

            else:

                recommendation_status = (
                    "Recommended"
                )

            recommendation = {
                "employee_id": employee_id,
                "employee_name": employee_name,
                "shift": employee_shift,
                "station_id": station_id,
                "station_name": station_name,
                "skill_score": skill_score,
                "verified_skill_count": verified_skill_count,
                "average_proficiency": round(
                    average_proficiency, 2
                ),
                "is_all_rounder": is_all_rounder,
                "mandatory_skills_met": mandatory_met,
                "missing_mandatory_skills": ", ".join(
                    missing_skills
                ),
                "current_station_usage": current_usage,
                "station_capacity": capacity,
                "capacity_available": capacity_available,
                "recommendation_status": recommendation_status
            }

            recommendations.append(recommendation)

            if mandatory_met:

                employee_options.append(
                    recommendation
                )

        # ---------------------------------------------
        # ELIGIBLE OPTIONS FOR THIS EMPLOYEE
        # ---------------------------------------------

        employee_options.sort(
            key=lambda item: item["skill_score"],
            reverse=True
        )

        for rank, option in enumerate(
            employee_options, start=1
        ):

            eligible_results.append({
                **option,
                "recommendation_rank": rank
            })

    # -------------------------------------------------
    # STEP 11: CREATE RESULT DATAFRAMES
    # -------------------------------------------------

    result = pd.DataFrame(recommendations)

    eligible_result = pd.DataFrame(
        eligible_results
    )

    if result.empty:

        print("No station recommendations generated.")

        return result, eligible_result

    # -------------------------------------------------
    # STEP 12: DISPLAY RESULTS
    # -------------------------------------------------

    print("\n========== STATION RECOMMENDATION REPORT ==========")

    print("Selected Date:", selected_date)

    print(
        "\nActive Present Employees:",
        len(available_employees)
    )

    print(
        "Verified Skill Records:",
        len(verified_skills)
    )

    print(
        "\n--- EMPLOYEE RECOMMENDATIONS ---"
    )

    for employee_id in available_employees[
        "employee_id"
    ].astype(str):

        employee_rows = result[
            result["employee_id"] == employee_id
        ]

        if employee_rows.empty:
            continue

        employee_name = employee_rows.iloc[0][
            "employee_name"
        ]

        print(
            f"\nEmployee: {employee_name} ({employee_id})"
        )

        print(
            employee_rows[
                [
                    "station_id",
                    "station_name",
                    "skill_score",
                    "recommendation_status"
                ]
            ].to_string(index=False)
        )

    # -------------------------------------------------
    # STEP 13: AVAILABLE RECOMMENDATION SHORTLIST
    # -------------------------------------------------

    shortlist = result[
        result["recommendation_status"] == "Recommended"
    ].copy()

    shortlist = shortlist.sort_values(
        by=["employee_id", "skill_score"],
        ascending=[True, False]
    )

    print(
        "\n========== AVAILABLE RECOMMENDATION SHORTLIST =========="
    )

    if shortlist.empty:

        print("No available station recommendations.")

    else:

        print(
            shortlist[
                [
                    "employee_id",
                    "employee_name",
                    "shift",
                    "station_id",
                    "station_name",
                    "skill_score",
                    "is_all_rounder"
                ]
            ].to_string(index=False)
        )

    # -------------------------------------------------
    # STEP 14: ALREADY ALLOCATED EMPLOYEES
    # -------------------------------------------------

    allocated_employees = (
        result[
            result["recommendation_status"]
            == "Already Allocated"
        ][
            [
                "employee_id",
                "employee_name",
                "shift"
            ]
        ]
        .drop_duplicates()
    )

    print(
        "\n========== ALREADY ALLOCATED EMPLOYEES =========="
    )

    if allocated_employees.empty:
        print("No employees are currently allocated.")

    else:
        print(
            allocated_employees.to_string(index=False)
        )

    # -------------------------------------------------
    # STEP 15: EMPLOYEES WITHOUT ELIGIBLE STATIONS
    # -------------------------------------------------

    eligible_employee_ids = set(
        eligible_result["employee_id"]
        if not eligible_result.empty
        else []
    )

    unavailable_employees = available_employees[
        ~available_employees["employee_id"]
        .astype(str)
        .isin(eligible_employee_ids)
    ]

    print(
        "\n========== EMPLOYEES WITHOUT ELIGIBLE STATIONS =========="
    )

    if unavailable_employees.empty:

        print("All present employees have at least one eligible station.")

    else:

        print(
            unavailable_employees[
                [
                    "employee_id",
                    "employee_name",
                    "shift"
                ]
            ].to_string(index=False)
        )

    print(
        "\n========== RECOMMENDATION GENERATION COMPLETED =========="
    )

    print("Master data was read from PostgreSQL.")
    print("No PostgreSQL records were modified.")

    return result, eligible_result


if __name__ == "__main__":

    generate_station_recommendations(
        recommendation_date="2026-11-04"
    )
