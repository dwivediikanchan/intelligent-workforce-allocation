import pandas as pd

from database_repository import (
    get_stations,
    get_station_requirements
)


def analyze_station_requirements():

    # ==========================================
    # STEP 1: LOAD DATA FROM POSTGRESQL
    # ==========================================

    stations = get_stations()
    requirements = get_station_requirements()

    print("\n========== STATION REQUIREMENT ANALYSIS ==========")

    print("Station master data: PostgreSQL")
    print("Station requirements: PostgreSQL")

    if stations.empty:
        print("ERROR: No station records found.")
        return

    if requirements.empty:
        print("ERROR: No station requirement records found.")
        return

    # ==========================================
    # STEP 2: DISPLAY STATION REQUIREMENTS
    # ==========================================

    print("\n--- STATION SKILL REQUIREMENTS ---")

    print(requirements.to_string(index=False))

    # ==========================================
    # STEP 3: MERGE WITH STATION INFORMATION
    # ==========================================

    station_matrix = requirements.merge(
        stations,
        on="station_id",
        how="left"
    )

    print("\n--- COMPLETE STATION MATRIX ---")

    print(
        station_matrix[
            [
                "station_id",
                "station_name",
                "skill_name",
                "min_proficiency",
                "weight",
                "mandatory"
            ]
        ].to_string(index=False)
    )

    # ==========================================
    # STEP 4: COUNT MANDATORY SKILLS
    # ==========================================

    mandatory_skills = (
        requirements[
            requirements["mandatory"].astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes"])
        ]
        .groupby("station_id")
        .size()
        .reset_index(name="mandatory_skill_count")
    )

    print("\n--- MANDATORY SKILLS PER STATION ---")

    print(mandatory_skills.to_string(index=False))

    # ==========================================
    # STEP 5: FINAL STATUS
    # ==========================================

    print("\nStation master data: PostgreSQL")
    print("Station requirements: PostgreSQL")
    print("No PostgreSQL records were modified.")

    print("\n========== ANALYSIS COMPLETED ==========")


if __name__ == "__main__":
    analyze_station_requirements()