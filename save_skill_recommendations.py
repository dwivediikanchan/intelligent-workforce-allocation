
import pandas as pd

from datetime import datetime

from sqlalchemy import select

from database_repository import (
    get_employees,
    get_employee_skills,
    get_stations,
    get_station_requirements,
    get_attendance,
    get_allocations
)

from database_connection import SessionLocal

from database_models import SkillVerificationRecommendation


def save_skill_recommendations():

    print("\n========== GENERATE SKILL RECOMMENDATIONS ==========")

    # ------------------------------------------
    # STEP 1: SELECT ALLOCATION DATE
    # ------------------------------------------

    selected_date = input(
        "\nEnter allocation date (YYYY-MM-DD) [2026-11-04]: "
    ).strip()

    if not selected_date:
        selected_date = "2026-11-04"

    try:
        allocation_date = datetime.strptime(
            selected_date, "%Y-%m-%d"
        ).date()

    except ValueError:
        print("\nInvalid date format.")
        return

    # ------------------------------------------
    # STEP 2: LOAD DATA FROM POSTGRESQL
    # ------------------------------------------

    try:
        employees = get_employees()
        employee_skills = get_employee_skills()
        stations = get_stations()
        requirements = get_station_requirements()
        attendance = get_attendance()
        allocations = get_allocations()

    except Exception as error:
        print("\nDatabase data loading failed:", error)
        return

    print("\nPostgreSQL data loaded successfully.")

    # ------------------------------------------
    # STEP 3: FIND PRESENT EMPLOYEES
    # WHO HAVE NO ALLOCATION
    # ------------------------------------------

    if employees.empty or attendance.empty:
        print("\nNo employee or attendance data available.")
        return

    employees = employees[
        employees["status"].astype(str).str.lower() == "active"
    ].copy()

    attendance["attendance_date"] = pd.to_datetime(
        attendance["attendance_date"]
    ).dt.date

    daily_attendance = attendance[
        (attendance["attendance_date"] == allocation_date)
        & (
            attendance["attendance_status"]
            .astype(str)
            .str.lower() == "present"
        )
    ].copy()

    available_employees = employees.merge(
        daily_attendance[
            ["employee_id", "shift"]
        ],
        on=["employee_id", "shift"],
        how="inner"
    )

    if not allocations.empty:

        allocations["allocation_date"] = pd.to_datetime(
            allocations["allocation_date"]
        ).dt.date

        active_allocations = allocations[
            (allocations["allocation_date"] == allocation_date)
            & (
                allocations["status"]
                .astype(str)
                .str.lower() == "allocated"
            )
        ]

        allocated_pairs = set(
            zip(
                active_allocations["employee_id"],
                active_allocations["shift"]
            )
        )

    else:
        allocated_pairs = set()

    unallocated = available_employees[
        ~available_employees.apply(
            lambda row: (
                row["employee_id"], row["shift"]
            ) in allocated_pairs,
            axis=1
        )
    ].copy()

    print("\nSelected date:", allocation_date)
    print("Present employees:", len(available_employees))
    print("Present but unallocated:", len(unallocated))

    if unallocated.empty:
        print("\nNo present unallocated employees found.")
        return

    # ------------------------------------------
    # STEP 4: GENERATE SKILL RECOMMENDATIONS
    # ------------------------------------------

    new_recommendations = []

    for _, employee in unallocated.iterrows():

        emp_id = employee["employee_id"]
        emp_name = employee["employee_name"]

        emp_skills = employee_skills[
            employee_skills["employee_id"] == emp_id
        ]

        for _, station in stations.iterrows():

            station_id = station["station_id"]

            rules = requirements[
                (requirements["station_id"] == station_id)
                & (
                    requirements["mandatory"]
                    .astype(str)
                    .str.lower()
                    .isin(["true", "1", "yes"])
                )
            ]

            if rules.empty:
                continue

            verification_needed = []
            training_needed = []
            missing_skills = []

            for _, rule in rules.iterrows():

                skill_name = rule["skill_name"]
                minimum = float(rule["min_proficiency"])

                record = emp_skills[
                    emp_skills["skill_name"]
                    .astype(str)
                    .str.lower()
                    == str(skill_name).lower()
                ]

                if record.empty:

                    missing_skills.append(skill_name)

                else:

                    skill_record = record.iloc[0]

                    level = float(
                        skill_record["proficiency_level"]
                    )

                    status = str(
                        skill_record["verification_status"]
                    ).strip()

                    if level < minimum:

                        training_needed.append(skill_name)

                    elif status.lower() != "verified":

                        verification_needed.append(skill_name)

            # Recommend verification only when:
            # 1. Skill records exist.
            # 2. Required proficiency is achieved.
            # 3. Verification is still pending.

            if (
                verification_needed
                and not training_needed
                and not missing_skills
            ):

                new_recommendations.append({
                    "employee_id": emp_id,
                    "employee_name": emp_name,
                    "recommended_station": station_id,
                    "skills_to_verify": verification_needed
                })

    # ------------------------------------------
    # STEP 5: SAVE TO POSTGRESQL
    # ------------------------------------------

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:

        with db.begin():

            existing = db.execute(
                select(
                    SkillVerificationRecommendation.employee_id,
                    SkillVerificationRecommendation.recommended_station
                ).where(
                    SkillVerificationRecommendation.recommendation_status.in_([
                        "Pending Manager Approval",
                        "Approved - Verification Required"
                    ])
                )
            ).all()

            existing_pairs = set(existing)

            for item in new_recommendations:

                employee_id = item["employee_id"]
                station_id = item["recommended_station"]

                pair = (employee_id, station_id)

                if pair in existing_pairs:
                    skipped += 1
                    continue

                recommendation = SkillVerificationRecommendation(
                    employee_id=employee_id,
                    recommended_station=station_id,
                    skills_to_verify=item["skills_to_verify"],
                    recommendation_status="Pending Manager Approval"
                )

                db.add(recommendation)

                existing_pairs.add(pair)
                inserted += 1

        # ------------------------------------------
        # STEP 6: DISPLAY RESULTS
        # ------------------------------------------

        print("\n========== RECOMMENDATION SUMMARY ==========")

        if new_recommendations:

            print("\nGenerated Recommendations:\n")

            for item in new_recommendations:

                print(
                    f"Employee: {item['employee_id']} | "
                    f"Name: {item['employee_name']} | "
                    f"Station: {item['recommended_station']} | "
                    f"Skills: {', '.join(item['skills_to_verify'])}"
                )

        else:

            print("\nNo new skill verification recommendations generated.")

        print("\nNew recommendations saved:", inserted)
        print("Duplicate recommendations skipped:", skipped)

        print("\nRecommendations stored in PostgreSQL.")
        print("\n========== PROCESS COMPLETED ==========")

    except Exception as error:

        db.rollback()

        print("\nRecommendation generation failed:", error)

    finally:

        db.close()


if __name__ == "__main__":
    save_skill_recommendations()
