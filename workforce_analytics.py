
import pandas as pd
import plotly.express as px
import streamlit as st


def show_workforce_analytics(
    employees_df,
    recommendations_df,
    manager_selection_df=None
):
    """
    Display workforce analytics using uploaded employee
    and recommendation data.

    Does not modify existing project CSV files.
    """

    st.title("📊 Workforce Analytics Dashboard")

    st.caption(
        "Interactive analysis of employee availability, "
        "station eligibility and proposed allocations."
    )

    # =========================================
    # 1. VALIDATE INPUTS
    # =========================================

    if not isinstance(employees_df, pd.DataFrame):
        st.error("Employee data must be a DataFrame.")
        return

    if not isinstance(recommendations_df, pd.DataFrame):
        st.error("Recommendation data must be a DataFrame.")
        return

    if employees_df.empty:
        st.warning("No employee records available.")
        return

    if recommendations_df.empty:
        st.warning("No recommendation records available.")
        return

    required_employee_columns = {
        "employee_id",
        "employee_name",
        "shift",
        "status"
    }

    required_recommendation_columns = {
        "employee_id",
        "employee_name",
        "shift",
        "station_id",
        "station_name",
        "skill_score",
        "recommendation_status",
        "capacity_status"
    }

    missing_employees = (
        required_employee_columns - set(employees_df.columns)
    )

    missing_recommendations = (
        required_recommendation_columns - set(recommendations_df.columns)
    )

    if missing_employees:
        st.error(
            f"Missing employee columns: {sorted(missing_employees)}"
        )
        return

    if missing_recommendations:
        st.error(
            "Missing recommendation columns: "
            f"{sorted(missing_recommendations)}"
        )
        return

    employees = employees_df.copy()
    recommendations = recommendations_df.copy()

    # =========================================
    # 2. NORMALIZE DATA
    # =========================================

    employees["employee_id"] = (
        employees["employee_id"].astype(str).str.strip()
    )

    employees["shift"] = (
        employees["shift"].astype(str).str.strip().str.title()
    )

    employees["status"] = (
        employees["status"].astype(str).str.strip().str.title()
    )

    recommendations["employee_id"] = (
        recommendations["employee_id"]
        .astype(str)
        .str.strip()
    )

    recommendations["shift"] = (
        recommendations["shift"].astype(str).str.strip().str.title()
    )

    recommendations["recommendation_status"] = (
        recommendations["recommendation_status"]
        .astype(str).str.strip()
    )

    recommendations["capacity_status"] = (
        recommendations["capacity_status"]
        .astype(str).str.strip()
    )

    recommendations["skill_score"] = pd.to_numeric(
        recommendations["skill_score"],
        errors="coerce"
    ).fillna(0)

    # =========================================
    # 3. FILTER ACTIVE EMPLOYEES
    # =========================================

    active_employees = employees[
        employees["status"].eq("Active")
    ].copy()

    recommended = recommendations[
        recommendations["recommendation_status"].eq("Recommended")
    ].copy()

    within_capacity = recommended[
        recommended["capacity_status"].eq("Within Capacity")
    ].copy()

    capacity_exceeded = recommended[
        recommended["capacity_status"].eq("Capacity Exceeded")
    ].copy()

    eligible_employee_ids = set(
        recommended["employee_id"].unique()
    )

    unavailable = recommendations[
        recommendations["recommendation_status"].eq("Unavailable")
    ]

    unavailable_employee_ids = set(
        unavailable["employee_id"].unique()
    )

    active_ids = set(active_employees["employee_id"])

    # Count unique active employees with at least one eligible option.
    employees_with_options = len(
        eligible_employee_ids.intersection(active_ids)
    )

    employees_without_options = max(
        len(active_employees) - employees_with_options,
        0
    )

    # =========================================
    # 4. KPI METRICS
    # =========================================

    st.subheader("Workforce Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Active Employees",
        len(active_employees)
    )

    col2.metric(
        "Employees With Options",
        employees_with_options
    )

    col3.metric(
        "Employees Without Options",
        employees_without_options
    )

    col4.metric(
        "Eligible Station Options",
        len(recommended)
    )

    st.divider()

    # =========================================
    # 5. SHIFT-WISE WORKFORCE DISTRIBUTION
    # =========================================

    st.subheader("1. Shift-wise Workforce Distribution")

    shift_data = (
        active_employees
        .groupby("shift")
        .size()
        .reset_index(name="employee_count")
    )

    if not shift_data.empty:

        fig_shift = px.bar(
            shift_data,
            x="shift",
            y="employee_count",
            color="shift",
            text="employee_count",
            title="Active Employees by Shift",
            labels={
                "shift": "Shift",
                "employee_count": "Number of Employees"
            }
        )

        st.plotly_chart(
            fig_shift,
            use_container_width=True
        )

    # =========================================
    # 6. STATION-WISE ELIGIBILITY
    # =========================================

    st.subheader("2. Station-wise Skill Eligibility")

    if not recommended.empty:

        station_data = (
            recommended
            .groupby(["station_id", "station_name"])
            ["employee_id"]
            .nunique()
            .reset_index(name="eligible_employees")
        )

        fig_station = px.bar(
            station_data,
            x="station_name",
            y="eligible_employees",
            color="station_name",
            text="eligible_employees",
            title="Employees Eligible for Each Station",
            labels={
                "station_name": "Station",
                "eligible_employees": "Eligible Employees"
            }
        )

        st.plotly_chart(
            fig_station,
            use_container_width=True
        )

    else:

        st.info("No eligible station recommendations available.")

    # =========================================
    # 7. RECOMMENDATION STATUS
    # =========================================

    st.subheader("3. Recommendation Status Distribution")

    status_data = (
        recommendations
        .groupby("recommendation_status")
        .size()
        .reset_index(name="record_count")
    )

    fig_status = px.pie(
        status_data,
        names="recommendation_status",
        values="record_count",
        hole=0.45,
        title="Recommendation Status"
    )

    st.plotly_chart(
        fig_status,
        use_container_width=True
    )

    # =========================================
    # 8. CAPACITY ANALYSIS
    # =========================================

    st.subheader("4. Station Capacity Analysis")

    if not recommended.empty:

        capacity_data = (
            recommended
            .groupby(
                ["station_id", "station_name", "shift"]
            )
            .agg(
                eligible_candidates=(
                    "employee_id",
                    "nunique"
                ),
                station_capacity=(
                    "station_capacity",
                    "first"
                )
            )
            .reset_index()
        )

        if "station_capacity" not in recommended.columns:

            st.warning(
                "Station capacity data is unavailable."
            )

        else:

            capacity_data["capacity_status"] = (
                capacity_data.apply(
                    lambda row: (
                        "Within Capacity"
                        if row["eligible_candidates"]
                        <= row["station_capacity"]
                        else "Capacity Exceeded"
                    ),
                    axis=1
                )
            )

            fig_capacity = px.bar(
                capacity_data,
                x="station_name",
                y="eligible_candidates",
                color="capacity_status",
                barmode="group",
                facet_col="shift",
                text="eligible_candidates",
                title="Eligible Candidates vs Station Capacity",
                labels={
                    "station_name": "Station",
                    "eligible_candidates": "Eligible Candidates",
                    "capacity_status": "Capacity Status"
                }
            )

            st.plotly_chart(
                fig_capacity,
                use_container_width=True
            )

            st.dataframe(
                capacity_data,
                use_container_width=True,
                hide_index=True
            )

    # =========================================
    # 9. SKILL SCORE ANALYSIS
    # =========================================

    st.subheader("5. Employee Skill Score Analysis")

    if not recommended.empty:

        score_data = recommended.sort_values(
            "skill_score",
            ascending=False
        )

        fig_scores = px.bar(
            score_data,
            x="employee_name",
            y="skill_score",
            color="station_name",
            barmode="group",
            hover_data=[
                "employee_id",
                "shift",
                "station_id"
            ],
            title="Employee Skill Match Scores",
            labels={
                "employee_name": "Employee",
                "skill_score": "Skill Match Score",
                "station_name": "Station"
            }
        )

        st.plotly_chart(
            fig_scores,
            use_container_width=True
        )

    # =========================================
    # 10. MANAGER SELECTION ANALYSIS
    # =========================================

    st.subheader("6. Manager Proposed Allocation Analysis")

    if (
        isinstance(manager_selection_df, pd.DataFrame)
        and not manager_selection_df.empty
    ):

        manager_data = manager_selection_df.copy()

        shift_station_data = (
            manager_data
            .groupby(
                ["station_name", "shift"]
            )
            .size()
            .reset_index(name="selected_employees")
        )

        fig_manager = px.bar(
            shift_station_data,
            x="station_name",
            y="selected_employees",
            color="shift",
            barmode="group",
            text="selected_employees",
            title="Manager-selected Employees by Station",
            labels={
                "station_name": "Station",
                "selected_employees": "Selected Employees",
                "shift": "Shift"
            }
        )

        st.plotly_chart(
            fig_manager,
            use_container_width=True
        )

        st.write("Manager Selection Details")

        st.dataframe(
            manager_data,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Manager selection has not been confirmed yet."
        )

    # =========================================
    # 11. EMPLOYEES WITHOUT ELIGIBLE OPTIONS
    # =========================================

    st.subheader("7. Employees Without Eligible Stations")

    no_option_ids = (
        active_ids - eligible_employee_ids
    )

    no_option_employees = active_employees[
        active_employees["employee_id"].isin(no_option_ids)
    ]

    if not no_option_employees.empty:

        st.warning(
            f"{len(no_option_employees)} active employee(s) "
            "have no eligible station recommendation."
        )

        st.dataframe(
            no_option_employees[
                ["employee_id", "employee_name", "shift"]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "All active employees have at least one eligible "
            "station option."
        )

    # =========================================
    # 12. DOWNLOAD ANALYTICS DATA
    # =========================================

    st.divider()

    st.subheader("Download Analytics Data")

    st.download_button(
        "Download Analytics Recommendations",
        data=recommendations.to_csv(index=False),
        file_name="workforce_analytics_report.csv",
        mime="text/csv"
    )
