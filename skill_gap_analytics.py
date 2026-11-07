
import pandas as pd
import plotly.express as px
import streamlit as st

from database_repository import get_station_requirements


def show_skill_gap_analytics(
    employees_df,
    skills_df
):
    """
    Analyze uploaded employee skills against
    station requirements stored in PostgreSQL.

    Tracks training gaps and verification gaps independently.
    A skill can have both gaps simultaneously.

    Uploaded employee and skill data are processed in memory.
    No existing project files are modified.
    """

    st.title("🎯 Employee Skill Gap Analysis")

    st.caption(
        "Identify workforce skill shortages, verification "
        "requirements and employee training opportunities."
    )

    # =========================================
    # 1. VALIDATE INPUTS
    # =========================================

    if not isinstance(employees_df, pd.DataFrame):
        st.error("Employee data must be a DataFrame.")
        return

    if not isinstance(skills_df, pd.DataFrame):
        st.error("Employee skills data must be a DataFrame.")
        return

    if employees_df.empty:
        st.warning("No employee records available.")
        return

    required_employee_columns = {
        "employee_id", "employee_name", "shift", "status"
    }

    required_skill_columns = {
        "employee_id", "skill_name",
        "proficiency_level", "verification_status"
    }

    if not required_employee_columns.issubset(employees_df.columns):
        st.error("Employee dataset is missing required columns.")
        return

    if not required_skill_columns.issubset(skills_df.columns):
        st.error("Employee skills dataset is missing required columns.")
        return

    # =========================================
    # 2. LOAD STATION REQUIREMENTS FROM POSTGRESQL
    # =========================================

    try:
        requirements_df = get_station_requirements()

    except Exception as error:
        st.error(
            f"Unable to load station requirements from PostgreSQL: {error}"
        )
        return

    if requirements_df.empty:
        st.warning("No station requirements found in PostgreSQL.")
        return

    required_requirement_columns = {
        "station_id", "skill_name",
        "min_proficiency", "weight", "mandatory"
    }

    if not required_requirement_columns.issubset(
        requirements_df.columns
    ):
        st.error(
            "PostgreSQL station requirements have missing columns."
        )
        return

    # =========================================
    # 3. NORMALIZE DATA
    # =========================================

    employees = employees_df.copy()
    skills = skills_df.copy()
    requirements = requirements_df.copy()

    for dataframe in [employees, skills, requirements]:
        for column in dataframe.select_dtypes(
            include=["object", "string"]
        ).columns:
            dataframe[column] = (
                dataframe[column].astype(str).str.strip()
            )

    employees["employee_id"] = (
        employees["employee_id"].astype(str).str.strip()
    )

    skills["employee_id"] = (
        skills["employee_id"].astype(str).str.strip()
    )

    skills["skill_name"] = skills["skill_name"].str.lower()
    requirements["skill_name"] = requirements["skill_name"].str.lower()

    skills["proficiency_level"] = pd.to_numeric(
        skills["proficiency_level"],
        errors="coerce"
    )

    requirements["min_proficiency"] = pd.to_numeric(
        requirements["min_proficiency"],
        errors="coerce"
    )

    requirements = requirements.dropna(
        subset=["station_id", "skill_name", "min_proficiency"]
    )

    requirements["mandatory"] = (
        requirements["mandatory"]
        .astype(str)
        .str.lower()
        .isin(["true", "1", "yes"])
    )

    skills["verification_status"] = (
        skills["verification_status"]
        .fillna("Pending")
        .astype(str)
        .str.strip()
        .str.title()
    )

    # =========================================
    # 4. FILTER ACTIVE EMPLOYEES
    # =========================================

    active_employees = employees[
        employees["status"].str.lower().eq("active")
    ].copy()

    if active_employees.empty:
        st.warning("No active employees available for analysis.")
        return

    # =========================================
    # 5. BUILD EMPLOYEE SKILL GAP REPORT
    # =========================================

    skill_gap_records = []

    for _, employee in active_employees.iterrows():

        employee_id = employee["employee_id"]

        employee_skills = skills[
            skills["employee_id"].eq(employee_id)
        ]

        for _, requirement in requirements.iterrows():

            skill_name = requirement["skill_name"]
            station_id = requirement["station_id"]
            minimum_level = requirement["min_proficiency"]

            matching_skills = employee_skills[
                employee_skills["skill_name"].eq(skill_name)
            ]

            if matching_skills.empty:

                actual_level = 0
                verification_status = "Missing"

            else:

                skill_record = matching_skills.iloc[-1]

                actual_level = skill_record["proficiency_level"]

                if pd.isna(actual_level):
                    actual_level = 0

                verification_status = (
                    skill_record["verification_status"]
                )

            # ---------------------------------
            # INDEPENDENT GAP CALCULATIONS
            # ---------------------------------

            needs_training = (
                actual_level < minimum_level
            )

            needs_verification = (
                verification_status != "Verified"
                and verification_status != "Missing"
            )

            if verification_status == "Missing":
                needs_verification = False

            if needs_training and needs_verification:
                gap_status = "Training + Verification Required"

            elif needs_training:
                gap_status = "Training Required"

            elif needs_verification:
                gap_status = "Verification Required"

            else:
                gap_status = "Skill Verified"

            skill_gap_records.append({

                "employee_id": employee_id,

                "employee_name": employee["employee_name"],

                "shift": employee["shift"],

                "station_id": station_id,

                "skill_name": skill_name,

                "required_proficiency": minimum_level,

                "actual_proficiency": actual_level,

                "proficiency_gap": max(
                    minimum_level - actual_level,
                    0
                ),

                "mandatory": requirement["mandatory"],

                "verification_status": verification_status,

                "needs_training": needs_training,

                "needs_verification": needs_verification,

                "gap_status": gap_status

            })

    gap_df = pd.DataFrame(skill_gap_records)

    if gap_df.empty:
        st.info("No skill requirements available for analysis.")
        return

    # =========================================
    # 6. CALCULATE SUMMARY METRICS
    # =========================================

    training_gaps = gap_df[
        gap_df["needs_training"]
    ]

    verification_gaps = gap_df[
        gap_df["needs_verification"]
    ]

    combined_gaps = gap_df[
        gap_df["needs_training"]
        & gap_df["needs_verification"]
    ]

    verified_skills = gap_df[
        gap_df["gap_status"].eq("Skill Verified")
    ]

    mandatory_gaps = gap_df[
        gap_df["mandatory"]
        & (
            gap_df["needs_training"]
            | gap_df["needs_verification"]
        )
    ]

    # =========================================
    # 7. DISPLAY KPI METRICS
    # =========================================

    st.subheader("Workforce Skill Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Active Employees", len(active_employees))
    col2.metric("Training Gaps", len(training_gaps))
    col3.metric("Verification Gaps", len(verification_gaps))
    col4.metric("Verified Requirements", len(verified_skills))

    st.metric(
        "Requirements Needing Both Training and Verification",
        len(combined_gaps)
    )

    st.divider()

    # =========================================
    # 8. SKILL GAP STATUS DISTRIBUTION
    # =========================================

    st.subheader("1. Skill Gap Status Distribution")

    status_summary = (
        gap_df.groupby("gap_status")
        .size()
        .reset_index(name="requirement_count")
    )

    fig_status = px.pie(
        status_summary,
        names="gap_status",
        values="requirement_count",
        hole=0.45,
        title="Employee Skill Requirement Status"
    )

    st.plotly_chart(fig_status, use_container_width=True)

    # =========================================
    # 9. EMPLOYEE-WISE TRAINING REQUIREMENTS
    # =========================================

    st.subheader("2. Employee-wise Training Requirements")

    if not training_gaps.empty:

        employee_training = (
            training_gaps.groupby("employee_name")
            .size()
            .reset_index(name="training_requirements")
            .sort_values(
                "training_requirements",
                ascending=False
            )
        )

        fig_training = px.bar(
            employee_training,
            x="employee_name",
            y="training_requirements",
            text="training_requirements",
            title="Training Requirements by Employee"
        )

        st.plotly_chart(fig_training, use_container_width=True)

    else:
        st.success("No training gaps identified.")

    # =========================================
    # 10. STATION-WISE SKILL SHORTAGES
    # =========================================

    st.subheader("3. Station-wise Skill Shortages")

    station_gaps = (
        training_gaps.groupby("station_id")
        .size()
        .reset_index(name="training_gaps")
    )

    if not station_gaps.empty:

        fig_station = px.bar(
            station_gaps,
            x="station_id",
            y="training_gaps",
            color="station_id",
            text="training_gaps",
            title="Training Gaps by Station"
        )

        st.plotly_chart(fig_station, use_container_width=True)

    else:
        st.success("No station skill shortages identified.")

    # =========================================
    # 11. MANDATORY SKILL GAP ANALYSIS
    # =========================================

    st.subheader("4. Mandatory Skill Gap Analysis")

    if not mandatory_gaps.empty:

        st.warning(
            f"{len(mandatory_gaps)} mandatory requirement(s) "
            "need attention."
        )

        st.dataframe(
            mandatory_gaps,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.success(
            "All analyzed mandatory skill requirements are verified."
        )

    # =========================================
    # 12. EMPLOYEE TRAINING RECOMMENDATIONS
    # =========================================

    st.subheader("5. Employee Training Recommendations")

    if not training_gaps.empty:

        training_report = training_gaps[
            [
                "employee_id",
                "employee_name",
                "shift",
                "station_id",
                "skill_name",
                "actual_proficiency",
                "required_proficiency",
                "proficiency_gap",
                "mandatory",
                "verification_status"
            ]
        ].sort_values(
            ["employee_id", "station_id", "skill_name"]
        )

        st.dataframe(
            training_report,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No additional training recommendations.")

    # =========================================
    # 13. PENDING SKILL VERIFICATION
    # =========================================

    st.subheader("6. Pending Skill Verification")

    if not verification_gaps.empty:

        verification_report = verification_gaps[
            [
                "employee_id",
                "employee_name",
                "shift",
                "station_id",
                "skill_name",
                "actual_proficiency",
                "required_proficiency",
                "proficiency_gap",
                "verification_status",
                "needs_training"
            ]
        ].sort_values(
            ["employee_id", "station_id", "skill_name"]
        )

        st.dataframe(
            verification_report,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.success("No pending skill verification requirements.")

    # =========================================
    # 14. DOWNLOAD REPORT
    # =========================================

    st.divider()

    st.subheader("Download Skill Gap Report")

    st.download_button(
        "Download Employee Skill Gap Report",
        data=gap_df.to_csv(index=False),
        file_name="employee_skill_gap_report.csv",
        mime="text/csv"
    )
