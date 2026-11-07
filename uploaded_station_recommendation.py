
import pandas as pd

from database_repository import (
    get_stations,
    get_station_requirements
)


def generate_uploaded_station_recommendations(
    employees_df,
    skills_df,
    attendance_df,
    recommendation_date=None
):
    """
    Generate capacity-aware station recommendations
    using uploaded employee, skill and attendance data.

    Station master data and requirements are loaded
    from PostgreSQL.

    No actual employee allocation is performed.
    """

    # =================================================
    # 1. VALIDATE INPUT DATAFRAMES
    # =================================================

    required_employee_columns = {
        "employee_id", "employee_name",
        "shift", "status"
    }

    required_skill_columns = {
        "employee_id", "skill_name",
        "proficiency_level", "verification_status"
    }

    required_attendance_columns = {
        "employee_id", "attendance_date",
        "shift", "attendance_status"
    }

    input_data = [
        ("Employees", employees_df, required_employee_columns),
        ("Skills", skills_df, required_skill_columns),
        ("Attendance", attendance_df, required_attendance_columns)
    ]

    for name, df, required in input_data:

        if not isinstance(df, pd.DataFrame):
            raise ValueError(f"{name} data must be a DataFrame.")

        missing = required - set(df.columns)

        if missing:
            raise ValueError(
                f"{name} data is missing columns: {sorted(missing)}"
            )

    # =================================================
    # 2. LOAD STATION MASTER DATA FROM POSTGRESQL
    # =================================================

    try:
        stations = get_stations()
        requirements = get_station_requirements()

    except Exception as error:
        raise RuntimeError(
            f"Unable to load station data from PostgreSQL: {error}"
        ) from error

    if stations.empty:
        raise ValueError("No station records found in PostgreSQL.")

    if requirements.empty:
        raise ValueError("No station requirements found in PostgreSQL.")

    required_station_columns = {
        "station_id", "station_name", "capacity"
    }

    required_requirement_columns = {
        "station_id", "skill_name", "min_proficiency",
        "weight", "mandatory"
    }

    if not required_station_columns.issubset(stations.columns):
        raise ValueError("Station master data has missing columns.")

    if not required_requirement_columns.issubset(requirements.columns):
        raise ValueError("Station requirements have missing columns.")

    # =================================================
    # 3. COPY AND NORMALIZE INPUT DATA
    # =================================================

    employees = employees_df.copy()
    skills = skills_df.copy()
    attendance = attendance_df.copy()
    stations = stations.copy()
    requirements = requirements.copy()

    for df in [employees, skills, attendance]:
        df["employee_id"] = (
            df["employee_id"].astype(str).str.strip()
        )

    employees["shift"] = (
        employees["shift"].astype(str).str.strip().str.title()
    )

    employees["status"] = (
        employees["status"].astype(str).str.strip().str.title()
    )

    skills["skill_name"] = (
        skills["skill_name"].astype(str).str.strip().str.lower()
    )

    skills["verification_status"] = (
        skills["verification_status"]
        .astype(str).str.strip().str.title()
    )

    skills["proficiency_level"] = pd.to_numeric(
        skills["proficiency_level"],
        errors="coerce"
    )

    attendance["shift"] = (
        attendance["shift"].astype(str).str.strip().str.title()
    )

    attendance["attendance_status"] = (
        attendance["attendance_status"]
        .astype(str).str.strip().str.title()
    )

    attendance["attendance_date"] = pd.to_datetime(
        attendance["attendance_date"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    stations["station_id"] = (
        stations["station_id"].astype(str).str.strip()
    )

    requirements["station_id"] = (
        requirements["station_id"].astype(str).str.strip()
    )

    requirements["skill_name"] = (
        requirements["skill_name"].astype(str).str.strip().str.lower()
    )

    requirements["mandatory"] = (
        requirements["mandatory"]
        .astype(str).str.strip().str.lower()
        .map({"true": True, "false": False})
    )

    requirements["weight"] = pd.to_numeric(
        requirements["weight"], errors="coerce"
    )

    requirements["min_proficiency"] = pd.to_numeric(
        requirements["min_proficiency"], errors="coerce"
    )

    stations["capacity"] = pd.to_numeric(
        stations["capacity"], errors="coerce"
    )

    # =================================================
    # 4. VALIDATE STATION MASTER DATA
    # =================================================

    if (
        stations["station_id"].duplicated().any()
        or stations["capacity"].isna().any()
        or (stations["capacity"] < 0).any()
    ):
        raise ValueError(
            "Station IDs must be unique and capacities must be non-negative."
        )

    if requirements[
        ["weight", "min_proficiency", "mandatory"]
    ].isna().any().any():
        raise ValueError(
            "Station requirements contain invalid weights, "
            "minimum proficiency or mandatory values."
        )

    if (
        (requirements["weight"] < 0).any()
        or (requirements["min_proficiency"] < 1).any()
        or (requirements["min_proficiency"] > 5).any()
    ):
        raise ValueError("Invalid station requirement values.")

    # =================================================
    # 5. RECOMMENDATION DATE
    # =================================================

    if recommendation_date is None:
        recommendation_date = pd.Timestamp.today().strftime("%Y-%m-%d")
    else:
        recommendation_date = pd.to_datetime(
            recommendation_date
        ).strftime("%Y-%m-%d")

    # =================================================
    # 6. FILTER ACTIVE EMPLOYEES
    # =================================================

    employees = employees[
        employees["status"].eq("Active")
    ].copy()

    # =================================================
    # 7. FILTER VERIFIED SKILLS
    # =================================================

    skills = skills[
        skills["verification_status"].eq("Verified")
        & skills["proficiency_level"].between(1, 5)
    ].copy()

    # =================================================
    # 8. FILTER PRESENT EMPLOYEES
    # =================================================

    attendance_today = attendance[
        (attendance["attendance_date"] == recommendation_date)
        & (attendance["attendance_status"] == "Present")
    ].copy()

    # =================================================
    # 9. GENERATE SKILL-BASED RECOMMENDATIONS
    # =================================================

    results = []

    for _, employee in employees.iterrows():

        employee_id = employee["employee_id"]
        employee_name = employee["employee_name"]
        employee_shift = employee["shift"]

        present = attendance_today[
            (attendance_today["employee_id"] == employee_id)
            & (attendance_today["shift"] == employee_shift)
        ]

        if present.empty:

            results.append({
                "employee_id": employee_id,
                "employee_name": employee_name,
                "shift": employee_shift,
                "station_id": "-",
                "station_name": "-",
                "skill_score": 0,
                "station_capacity": 0,
                "eligible_candidates": 0,
                "capacity_rank": "-",
                "capacity_status": "Unavailable",
                "recommendation_status": "Unavailable",
                "reason": "Employee is not marked Present"
            })

            continue

        employee_skills = skills[
            skills["employee_id"] == employee_id
        ]

        skill_map = (
            employee_skills
            .drop_duplicates("skill_name", keep="last")
            .set_index("skill_name")["proficiency_level"]
            .to_dict()
        )

        for _, station in stations.iterrows():

            station_id = station["station_id"]
            station_name = station["station_name"]
            station_capacity = int(station["capacity"])

            station_requirements = requirements[
                requirements["station_id"] == station_id
            ]

            if station_requirements.empty:
                continue

            mandatory_requirements = station_requirements[
                station_requirements["mandatory"]
            ]

            missing_skills = []

            for _, requirement in mandatory_requirements.iterrows():

                skill = requirement["skill_name"]
                minimum = requirement["min_proficiency"]

                employee_level = skill_map.get(skill)

                if (
                    employee_level is None
                    or employee_level < minimum
                ):
                    missing_skills.append(skill)

            if missing_skills:

                results.append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "shift": employee_shift,
                    "station_id": station_id,
                    "station_name": station_name,
                    "skill_score": 0,
                    "station_capacity": station_capacity,
                    "eligible_candidates": 0,
                    "capacity_rank": "-",
                    "capacity_status": "Not Applicable",
                    "recommendation_status": "Not Eligible",
                    "reason": (
                        "Missing mandatory skills: "
                        + ", ".join(missing_skills)
                    )
                })

                continue

            # Weighted skill score calculation

            total_weight = station_requirements["weight"].sum()

            if total_weight <= 0:
                raise ValueError(
                    f"Station {station_id} has zero total requirement weight."
                )

            achieved_score = 0

            for _, requirement in station_requirements.iterrows():

                skill = requirement["skill_name"]
                weight = requirement["weight"]

                employee_level = skill_map.get(skill, 0)

                achieved_score += (
                    min(employee_level / 5, 1)
                    * weight
                    * 100
                )

            score = round(
                achieved_score / total_weight,
                2
            )

            results.append({
                "employee_id": employee_id,
                "employee_name": employee_name,
                "shift": employee_shift,
                "station_id": station_id,
                "station_name": station_name,
                "skill_score": score,
                "station_capacity": station_capacity,
                "eligible_candidates": 0,
                "capacity_rank": 0,
                "capacity_status": "Pending",
                "recommendation_status": "Recommended",
                "reason": "All mandatory skills verified"
            })

    result_df = pd.DataFrame(results)

    # =================================================
    # 10. CAPACITY-AWARE SHORTLISTING
    # =================================================

    if result_df.empty:
        return result_df

    eligible_mask = result_df["recommendation_status"].eq(
        "Recommended"
    )

    eligible_results = result_df[eligible_mask].copy()

    if not eligible_results.empty:

        group_columns = ["station_id", "shift"]

        eligible_results["eligible_candidates"] = (
            eligible_results
            .groupby(group_columns)["employee_id"]
            .transform("count")
        )

        eligible_results = eligible_results.sort_values(
            by=[
                "station_id",
                "shift",
                "skill_score",
                "employee_id"
            ],
            ascending=[True, True, False, True]
        )

        eligible_results["capacity_rank"] = (
            eligible_results
            .groupby(group_columns)
            .cumcount() + 1
        )

        eligible_results["capacity_status"] = (
            eligible_results.apply(
                lambda row: (
                    "Within Capacity"
                    if row["capacity_rank"] <= row["station_capacity"]
                    else "Capacity Exceeded"
                ),
                axis=1
            )
        )

        result_df.loc[
            eligible_results.index,
            "eligible_candidates"
        ] = eligible_results["eligible_candidates"]

        result_df.loc[
            eligible_results.index,
            "capacity_rank"
        ] = eligible_results["capacity_rank"]

        result_df.loc[
            eligible_results.index,
            "capacity_status"
        ] = eligible_results["capacity_status"]

    # =================================================
    # 11. FINAL SORTING
    # =================================================

    result_df = result_df.sort_values(
        by=[
            "employee_id",
            "skill_score",
            "station_id"
        ],
        ascending=[True, False, True]
    ).reset_index(drop=True)

    return result_df
