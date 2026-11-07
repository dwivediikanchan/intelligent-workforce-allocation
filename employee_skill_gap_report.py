
import pandas as pd

from database_repository import (
    get_employee_skills,
    get_station_requirements,
    get_stations
)


def is_mandatory(value):
    return str(value).strip().lower() in ["true", "1", "yes"]


def generate_skill_gap_report():

    # ==========================================
    # STEP 1: LOAD DATA
    # ==========================================

    print("\n========== LOADING SKILL GAP DATA ==========")

    allocations = pd.read_csv("data/daily_allocations.csv")
    employee_skills = get_employee_skills()
    requirements = get_station_requirements()
    stations = get_stations()

    print("Daily allocation preview: CSV")
    print("Employee skills: PostgreSQL")
    print("Station requirements: PostgreSQL")
    print("Station master data: PostgreSQL")

    if allocations.empty:
        print("No daily allocation records found.")
        return

    if stations.empty or requirements.empty:
        print("ERROR: Station master data is unavailable.")
        return

    print("\n========== EMPLOYEE SKILL GAP REPORT ==========")

    # ==========================================
    # STEP 2: FIND PRESENT BUT UNALLOCATED
    # ==========================================

    unallocated = allocations[
        allocations["status"].astype(str).str.strip()
        == "Present - No Eligible Station"
    ]

    if unallocated.empty:
        print("No present but unallocated employees found.")

    for _, employee in unallocated.iterrows():

        emp_id = employee["employee_id"]
        emp_name = employee["employee_name"]

        print(f"\nEmployee: {emp_name} ({emp_id})")

        emp_skills = employee_skills[
            employee_skills["employee_id"] == emp_id
        ].copy()

        # ==========================================
        # STEP 3: STATION-WISE SKILL GAP ANALYSIS
        # ==========================================

        print("\n--- Station-wise Skill Gap Analysis ---")

        for _, station in stations.iterrows():

            station_id = station["station_id"]

            rules = requirements[
                (requirements["station_id"] == station_id)
                & requirements["mandatory"].apply(is_mandatory)
            ]

            gaps = []

            for _, rule in rules.iterrows():

                skill = rule["skill_name"]
                minimum = rule["min_proficiency"]

                record = emp_skills[
                    emp_skills["skill_name"] == skill
                ]

                if record.empty:

                    gaps.append(f"{skill}: Skill not recorded")
                    continue

                skill_record = record.iloc[0]

                level = skill_record["proficiency_level"]
                status = str(
                    skill_record["verification_status"]
                ).strip()

                if pd.isna(level) or level < minimum:

                    gaps.append(
                        f"{skill}: Training needed "
                        f"(Current {level}, Required {minimum})"
                    )

                elif status.lower() != "verified":

                    gaps.append(
                        f"{skill}: Verification needed "
                        f"(Current {level}, Required {minimum})"
                    )

            if gaps:

                print(f"\n{station_id} - Action Required:")

                for gap in gaps:
                    print(" -", gap)

            else:

                print(
                    f"{station_id}: Mandatory skills satisfied"
                )

        # ==========================================
        # STEP 4: GENERATE VERIFICATION RECOMMENDATIONS
        # ==========================================

        verification_recommendations = []

        for _, station in stations.iterrows():

            station_id = station["station_id"]

            rules = requirements[
                (requirements["station_id"] == station_id)
                & requirements["mandatory"].apply(is_mandatory)
            ]

            verification_needed = []
            training_needed = []
            missing_skills = []

            for _, rule in rules.iterrows():

                skill = rule["skill_name"]
                minimum = rule["min_proficiency"]

                record = emp_skills[
                    emp_skills["skill_name"] == skill
                ]

                if record.empty:

                    missing_skills.append(skill)
                    continue

                skill_record = record.iloc[0]

                level = skill_record["proficiency_level"]
                status = str(
                    skill_record["verification_status"]
                ).strip()

                if pd.isna(level) or level < minimum:

                    training_needed.append(skill)

                elif status.lower() != "verified":

                    verification_needed.append(skill)

            # Recommend stations where only verification is pending
            if (
                verification_needed
                and not training_needed
                and not missing_skills
            ):

                verification_recommendations.append({
                    "station_id": station_id,
                    "skills_to_verify": verification_needed
                })

        # ==========================================
        # STEP 5: DISPLAY RECOMMENDATIONS
        # ==========================================

        print("\n--- Recommended Actions ---")

        if verification_recommendations:

            for recommendation in verification_recommendations:

                skills = ", ".join(
                    recommendation["skills_to_verify"]
                )

                print(
                    f"Verify {skills} to make employee "
                    f"eligible for {recommendation['station_id']}."
                )

        else:

            print(
                "No verification-only recommendation available."
            )

    # ==========================================
    # STEP 6: FINAL STATUS
    # ==========================================

    print("\nDaily allocation preview: CSV")
    print("Employee and station master data: PostgreSQL")
    print("No PostgreSQL records were modified.")

    print("\n========== SKILL GAP ANALYSIS COMPLETED ==========")


if __name__ == "__main__":
    generate_skill_gap_report()
