
import pandas as pd
import streamlit as st
from datetime import date

from skill_gap_analytics import show_skill_gap_analytics
from workforce_upload import (
    load_workforce_file,
    validate_employee_skills,
    validate_attendance_file
)
from uploaded_station_recommendation import (
    generate_uploaded_station_recommendations
)
from workforce_analytics import show_workforce_analytics


def show_workforce_upload():

    st.title("📂 Workforce Data Upload")
    st.caption(
        "Upload employee, skills and attendance datasets "
        "to generate intelligent station recommendations."
    )
    st.divider()

    # -------------------------------------------------
    # 1. EMPLOYEE FILE UPLOAD
    # -------------------------------------------------

    st.subheader("1. Employee Workforce Data")

    employee_file = st.file_uploader(
        "Upload employee CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        key="central_employee_upload"
    )

    employee_df = None
    employee_errors = []

    if employee_file is not None:
        employee_df, employee_errors = load_workforce_file(
            employee_file
        )

        if employee_df is not None:
            st.write("Employee Data Preview")
            st.dataframe(employee_df, use_container_width=True)

            col1, col2 = st.columns(2)
            col1.metric("Total Employees", len(employee_df))
            col2.metric("Total Columns", len(employee_df.columns))

        if employee_errors:
            st.error("Employee validation failed.")
            for error in employee_errors:
                st.warning(error)
        elif employee_df is not None:
            st.success("Employee data passed validation!")

    st.divider()

    # -------------------------------------------------
    # 2. EMPLOYEE SKILLS UPLOAD
    # -------------------------------------------------

    st.subheader("2. Employee Skills Data")

    skills_file = st.file_uploader(
        "Upload employee skills CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        key="central_skills_upload"
    )

    skills_df = None
    skills_errors = []

    if skills_file is not None:
        skills_df, skills_errors = validate_employee_skills(
            skills_file,
            employee_df=employee_df
        )

        if skills_df is not None:
            st.write("Employee Skills Preview")
            st.dataframe(skills_df, use_container_width=True)

            col1, col2 = st.columns(2)
            col1.metric("Total Skill Records", len(skills_df))
            col2.metric(
                "Employees with Skills",
                skills_df["employee_id"].nunique()
            )

        if employee_df is None:
            st.warning(
                "Upload a valid employee file first to validate "
                "employee IDs against the skills file."
            )
        elif skills_errors:
            st.error("Employee skills validation failed.")
            for error in skills_errors:
                st.warning(error)
        elif skills_df is not None:
            st.success("Employee skills data passed validation!")

    st.divider()

    # -------------------------------------------------
    # 3. ATTENDANCE FILE UPLOAD
    # -------------------------------------------------

    st.subheader("3. Employee Attendance Data")

    attendance_file = st.file_uploader(
        "Upload attendance CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        key="central_attendance_upload"
    )

    attendance_df = None
    attendance_errors = []

    if attendance_file is not None:
        attendance_df, attendance_errors = validate_attendance_file(
            attendance_file,
            employee_df=employee_df
        )

        if attendance_df is not None:
            st.write("Attendance Data Preview")
            st.dataframe(attendance_df, use_container_width=True)

            col1, col2, col3 = st.columns(3)

            col1.metric("Attendance Records", len(attendance_df))
            col2.metric(
                "Employees Recorded",
                attendance_df["employee_id"].nunique()
            )

            present_count = (
                attendance_df["attendance_status"]
                .astype(str)
                .str.strip()
                .str.lower()
                .eq("present")
                .sum()
            )

            col3.metric("Present Employees", int(present_count))

        if employee_df is None:
            st.warning(
                "Upload a valid employee file first to validate "
                "attendance employee IDs."
            )
        elif attendance_errors:
            st.error("Attendance validation failed.")
            for error in attendance_errors:
                st.warning(error)
        elif attendance_df is not None:
            st.success("Attendance data passed validation!")

    st.divider()

    # -------------------------------------------------
    # 4. OVERALL VALIDATION
    # -------------------------------------------------

    st.subheader("4. Overall Validation Status")

    all_files_uploaded = (
        employee_file is not None
        and skills_file is not None
        and attendance_file is not None
    )

    all_data_valid = (
        employee_df is not None
        and skills_df is not None
        and attendance_df is not None
        and not employee_errors
        and not skills_errors
        and not attendance_errors
    )

    if not all_files_uploaded:
        st.info(
            "Upload all three files: employee, employee skills "
            "and attendance."
        )

    elif all_data_valid:
        st.success("All three datasets passed validation!")

        col1, col2, col3 = st.columns(3)
        col1.metric("Employees", len(employee_df))
        col2.metric("Skill Records", len(skills_df))
        col3.metric("Attendance Records", len(attendance_df))

    else:
        st.error(
            "Validation failed. Correct the errors before proceeding."
        )

    # -------------------------------------------------
    # 5. STATION RECOMMENDATIONS
    # -------------------------------------------------

    st.divider()
    st.subheader("5. Intelligent Station Recommendations")

    if all_data_valid:

        recommendation_date = st.date_input(
            "Select recommendation date",
            value=date.today(),
            key="central_recommendation_date"
        )

        if st.button(
            "Generate Station Recommendations",
            type="primary",
            use_container_width=True,
            key="central_generate_recommendations"
        ):
            try:
                with st.spinner(
                    "Analyzing employee skills and station requirements..."
                ):
                    recommendation_df = (
                        generate_uploaded_station_recommendations(
                            employees_df=employee_df,
                            skills_df=skills_df,
                            attendance_df=attendance_df,
                            recommendation_date=recommendation_date
                        )
                    )

                st.session_state[
                    "central_uploaded_recommendations"
                ] = recommendation_df

                st.session_state.pop(
                    "central_confirmed_manager_selection",
                    None
                )

                for key in list(st.session_state.keys()):
                    if key.startswith("central_manager_station_"):
                        del st.session_state[key]

                st.success("Station recommendations generated!")

            except Exception as error:
                st.error(f"Unable to generate recommendations: {error}")

    recommendation_df = st.session_state.get(
        "central_uploaded_recommendations"
    )

    if all_data_valid and recommendation_df is not None:

        st.markdown("### Recommendation Results")

        if recommendation_df.empty:
            st.warning("No recommendations were generated.")

        else:
            recommended_count = int(
                recommendation_df["recommendation_status"]
                .eq("Recommended").sum()
            )

            not_eligible_count = int(
                recommendation_df["recommendation_status"]
                .eq("Not Eligible").sum()
            )

            unavailable_count = int(
                recommendation_df["recommendation_status"]
                .eq("Unavailable").sum()
            )

            col1, col2, col3 = st.columns(3)
            col1.metric("Eligible Recommendations", recommended_count)
            col2.metric("Not Eligible", not_eligible_count)
            col3.metric("Unavailable Employees", unavailable_count)

            st.dataframe(
                recommendation_df,
                use_container_width=True,
                hide_index=True
            )

            st.download_button(
                "Download Recommendation Report",
                data=recommendation_df.to_csv(index=False),
                file_name="uploaded_station_recommendations.csv",
                mime="text/csv",
                key="central_download_recommendations"
            )

            st.info(
                "Recommendations are candidate options, not final "
                "allocations. Manager selections are checked against "
                "station capacity before confirmation."
            )

            # -----------------------------------------
            # 6. MANAGER STATION SELECTION
            # -----------------------------------------

            st.divider()
            st.subheader("6. Manager Station Selection")

            eligible_df = recommendation_df[
                recommendation_df["recommendation_status"].eq("Recommended")
            ].copy()

            if eligible_df.empty:
                st.warning("No eligible employees available for selection.")

            else:
                employee_groups = list(
                    eligible_df
                    .sort_values(
                        ["employee_id", "skill_score"],
                        ascending=[True, False]
                    )
                    .groupby("employee_id", sort=True)
                )

                for employee_id, group in employee_groups:

                    employee_row = group.iloc[0]

                    st.markdown(
                        f'**{employee_row["employee_name"]} '
                        f'({employee_id})** — {employee_row["shift"]} Shift'
                    )

                    options = ["-- Not selected --"]

                    for _, row in group.iterrows():
                        options.append(
                            f'{row["station_id"]} - '
                            f'{row["station_name"]} | '
                            f'Score: {row["skill_score"]} | '
                            f'Capacity: {row["station_capacity"]} | '
                            f'{row["capacity_status"]}'
                        )

                    st.selectbox(
                        f"Select station for {employee_id}",
                        options=options,
                        key=f"central_manager_station_{employee_id}"
                    )

                # -------------------------------------
                # 7. VALIDATE MANAGER SELECTIONS
                # -------------------------------------

                st.divider()
                st.subheader("7. Validate and Confirm Selection")

                if st.button(
                    "Validate and Confirm Manager Selection",
                    type="primary",
                    use_container_width=True,
                    key="central_validate_manager_selection"
                ):

                    selected_records = []

                    for employee_id, group in employee_groups:

                        employee_row = group.iloc[0]

                        selected_label = st.session_state.get(
                            f"central_manager_station_{employee_id}",
                            "-- Not selected --"
                        )

                        if selected_label == "-- Not selected --":
                            continue

                        selected_station_id = selected_label.split(" - ")[0]

                        selected_station = group[
                            group["station_id"].astype(str)
                            == str(selected_station_id)
                        ]

                        if selected_station.empty:
                            continue

                        selected_row = selected_station.iloc[0]

                        selected_records.append({
                            "employee_id": employee_id,
                            "employee_name": employee_row["employee_name"],
                            "shift": employee_row["shift"],
                            "station_id": selected_row["station_id"],
                            "station_name": selected_row["station_name"],
                            "skill_score": selected_row["skill_score"],
                            "station_capacity": int(
                                selected_row["station_capacity"]
                            )
                        })

                    selection_df = pd.DataFrame(selected_records)
                    validation_errors = []

                    if selection_df.empty:
                        validation_errors.append(
                            "Please select at least one station."
                        )

                    else:
                        if selection_df["employee_id"].duplicated().any():
                            validation_errors.append(
                                "An employee has been selected more than once."
                            )

                        capacity_usage = (
                            selection_df
                            .groupby(
                                ["station_id", "shift"],
                                as_index=False
                            )
                            .agg(
                                selected_employees=("employee_id", "count"),
                                station_capacity=("station_capacity", "min")
                            )
                        )

                        for _, row in capacity_usage.iterrows():
                            if row["selected_employees"] > row["station_capacity"]:
                                validation_errors.append(
                                    f'{row["station_id"]} ({row["shift"]}): '
                                    f'{row["selected_employees"]} selected, '
                                    f'capacity {row["station_capacity"]}.'
                                )

                    if validation_errors:
                        st.session_state.pop(
                            "central_confirmed_manager_selection",
                            None
                        )
                        st.error("Manager selection validation failed.")

                        for error in validation_errors:
                            st.warning(error)

                    else:
                        st.session_state[
                            "central_confirmed_manager_selection"
                        ] = selection_df.copy()

                        st.success(
                            "Manager selection passed validation!"
                        )

                # -------------------------------------
                # 8. CONFIRMED PROPOSED ASSIGNMENTS
                # -------------------------------------

                confirmed_df = st.session_state.get(
                    "central_confirmed_manager_selection"
                )

                if confirmed_df is not None:

                    st.divider()
                    st.subheader("Confirmed Proposed Station Assignments")

                    st.dataframe(
                        confirmed_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.metric("Employees Selected", len(confirmed_df))

                    st.download_button(
                        "Download Manager Selection",
                        data=confirmed_df.to_csv(index=False),
                        file_name="manager_station_selection.csv",
                        mime="text/csv",
                        key="central_download_manager_selection"
                    )

                    st.success(
                        "Proposed selections passed employee and "
                        "station capacity validation."
                    )

                    st.caption(
                        "These are proposals held in the current session. "
                        "They have not been saved as PostgreSQL allocations."
                    )

    # -------------------------------------------------
    # 9. WORKFORCE ANALYTICS
    # -------------------------------------------------

    st.divider()
    st.subheader("8. Workforce Analytics Dashboard")

    if all_data_valid and recommendation_df is not None:

        if st.checkbox(
            "Show Workforce Analytics Dashboard",
            value=False,
            key="central_show_workforce_analytics"
        ):

            confirmed_selection = st.session_state.get(
                "central_confirmed_manager_selection",
                pd.DataFrame()
            )

            try:
                show_workforce_analytics(
                    employees_df=employee_df,
                    recommendations_df=recommendation_df,
                    manager_selection_df=confirmed_selection
                )
            except Exception as error:
                st.error(f"Unable to display workforce analytics: {error}")

    else:
        st.info(
            "Upload and validate all three datasets, then generate "
            "recommendations to access workforce analytics."
        )

    # -------------------------------------------------
    # 10. EMPLOYEE SKILL GAP ANALYSIS
    # -------------------------------------------------

    st.divider()
    st.subheader("🎯 Employee Skill Gap Analysis")

    if st.checkbox(
        "Show Employee Skill Gap Dashboard",
        key="central_show_skill_gap_dashboard"
    ):

        if (
            all_data_valid
            and employee_df is not None
            and skills_df is not None
        ):
            try:
                show_skill_gap_analytics(
                    employees_df=employee_df,
                    skills_df=skills_df
                )
            except Exception as error:
                st.error(f"Unable to display skill gap analytics: {error}")
        else:
            st.warning(
                "Upload and validate employee and skill files first."
            )

    # -------------------------------------------------
    # DATA SAFETY NOTICE
    # -------------------------------------------------

    st.divider()

    st.caption(
        "Data safety: uploaded datasets are processed in memory. "
        "Manager selections remain in the current Streamlit session "
        "and can be downloaded. Existing database records and "
        "allocation data are not modified by this upload workflow."
    )
