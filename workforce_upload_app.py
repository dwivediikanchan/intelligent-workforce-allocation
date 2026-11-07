
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

from workforce_analytics import (
    show_workforce_analytics
)


st.set_page_config(
    page_title="Workforce Data Upload",
    page_icon="📂",
    layout="wide"
)

st.title("📂 Workforce Data Upload")

st.caption(
    "Upload employee, skills and attendance datasets "
    "to generate intelligent station recommendations."
)

st.divider()


# =====================================================
# 1. EMPLOYEE FILE UPLOAD
# =====================================================

st.subheader("1. Employee Workforce Data")

employee_file = st.file_uploader(
    "Upload employee CSV or Excel file",
    type=["csv", "xlsx", "xls"],
    key="employee_upload"
)

employee_df = None
employee_errors = []

if employee_file is not None:

    employee_df, employee_errors = load_workforce_file(
        employee_file
    )

    if employee_df is not None:

        st.write("Employee Data Preview")

        st.dataframe(
            employee_df,
            use_container_width=True
        )

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


# =====================================================
# 2. EMPLOYEE SKILLS UPLOAD
# =====================================================

st.subheader("2. Employee Skills Data")

skills_file = st.file_uploader(
    "Upload employee skills CSV or Excel file",
    type=["csv", "xlsx", "xls"],
    key="skills_upload"
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

        st.dataframe(
            skills_df,
            use_container_width=True
        )

        col1, col2 = st.columns(2)

        col1.metric("Total Skill Records", len(skills_df))

        col2.metric(
            "Employees with Skills",
            skills_df["employee_id"].nunique()
        )

    if employee_df is None:

        st.warning(
            "Upload a valid employee file first to check "
            "employee IDs against the skills file."
        )

    elif skills_errors:

        st.error("Employee skills validation failed.")

        for error in skills_errors:
            st.warning(error)

    elif skills_df is not None:

        st.success("Employee skills data passed validation!")


st.divider()


# =====================================================
# 3. ATTENDANCE FILE UPLOAD
# =====================================================

st.subheader("3. Employee Attendance Data")

attendance_file = st.file_uploader(
    "Upload attendance CSV or Excel file",
    type=["csv", "xlsx", "xls"],
    key="attendance_upload"
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

        st.dataframe(
            attendance_df,
            use_container_width=True
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Attendance Records",
            len(attendance_df)
        )

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

        col3.metric(
            "Present Employees",
            int(present_count)
        )

    if employee_df is None:

        st.warning(
            "Upload a valid employee file first to check "
            "attendance employee IDs."
        )

    elif attendance_errors:

        st.error("Attendance validation failed.")

        for error in attendance_errors:
            st.warning(error)

    elif attendance_df is not None:

        st.success("Attendance data passed validation!")


st.divider()


# =====================================================
# 4. OVERALL VALIDATION STATUS
# =====================================================

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
        "and attendance to complete validation."
    )

elif all_data_valid:

    st.success(
        "All three datasets passed validation successfully!"
    )

    st.markdown("### Validated Dataset Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric("Employees", len(employee_df))
    col2.metric("Skill Records", len(skills_df))
    col3.metric("Attendance Records", len(attendance_df))

else:

    st.error(
        "Validation failed. Please correct the errors "
        "before proceeding."
    )


# =====================================================
# 5. STATION RECOMMENDATION ENGINE
# =====================================================

st.divider()

st.subheader("5. Intelligent Station Recommendations")

if all_data_valid:

    st.write(
        "Generate station recommendations using uploaded "
        "employee skills, verification status and attendance."
    )

    recommendation_date = st.date_input(
        "Select recommendation date",
        value=date.today()
    )

    if st.button(
        "Generate Station Recommendations",
        type="primary",
        use_container_width=True
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

            st.session_state["uploaded_recommendations"] = (
                recommendation_df
            )

            # Clear previous manager selections
            for key in list(st.session_state.keys()):

                if key.startswith("manager_station_"):
                    del st.session_state[key]

            st.session_state.pop(
                "confirmed_manager_selection",
                None
            )

            st.success(
                "Station recommendations generated successfully!"
            )

        except Exception as error:

            st.error(
                f"Unable to generate recommendations: {error}"
            )

    # -------------------------------------------------
    # DISPLAY RECOMMENDATION RESULTS
    # -------------------------------------------------

    if "uploaded_recommendations" in st.session_state:

        recommendation_df = st.session_state[
            "uploaded_recommendations"
        ]

        st.markdown("### Recommendation Results")

        if recommendation_df.empty:

            st.warning("No recommendations were generated.")

        else:

            recommended_count = (
                recommendation_df["recommendation_status"]
                .eq("Recommended")
                .sum()
            )

            not_eligible_count = (
                recommendation_df["recommendation_status"]
                .eq("Not Eligible")
                .sum()
            )

            unavailable_count = (
                recommendation_df["recommendation_status"]
                .eq("Unavailable")
                .sum()
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Eligible Recommendations",
                int(recommended_count)
            )

            col2.metric(
                "Not Eligible",
                int(not_eligible_count)
            )

            col3.metric(
                "Unavailable Employees",
                int(unavailable_count)
            )

            st.dataframe(
                recommendation_df,
                use_container_width=True,
                hide_index=True
            )

            csv_data = recommendation_df.to_csv(index=False)

            st.download_button(
                "Download Recommendation Report",
                data=csv_data,
                file_name="uploaded_station_recommendations.csv",
                mime="text/csv"
            )

            st.info(
                "Capacity rankings are candidate shortlists. "
                "Manager selections are checked again against "
                "station capacity before confirmation."
            )

            # =========================================
            # 6. MANAGER STATION SELECTION
            # =========================================

            st.divider()

            st.subheader("6. Manager Station Selection")

            st.write(
                "Select one eligible station for each employee. "
                "Employees without eligible stations cannot be selected."
            )

            eligible_df = recommendation_df[
                recommendation_df["recommendation_status"]
                .eq("Recommended")
            ].copy()

            if eligible_df.empty:

                st.warning(
                    "There are no eligible employees available "
                    "for manager station selection."
                )

            else:

                employee_groups = (
                    eligible_df
                    .sort_values(
                        by=["employee_id", "skill_score"],
                        ascending=[True, False]
                    )
                    .groupby(
                        "employee_id",
                        sort=True
                    )
                )

                st.markdown("#### Choose stations")

                for employee_id, group in employee_groups:

                    employee_name = group.iloc[0]["employee_name"]
                    employee_shift = group.iloc[0]["shift"]

                    st.markdown(
                        f"**{employee_name} ({employee_id})** "
                        f"— {employee_shift} Shift"
                    )

                    options = ["-- Not selected --"]

                    for _, row in group.iterrows():

                        label = (
                            f'{row["station_id"]} - '
                            f'{row["station_name"]} | '
                            f'Score: {row["skill_score"]} | '
                            f'Capacity: {row["station_capacity"]} | '
                            f'{row["capacity_status"]}'
                        )

                        options.append(label)

                    st.selectbox(
                        f"Select station for {employee_id}",
                        options=options,
                        key=f"manager_station_{employee_id}"
                    )

                    st.divider()

                # =====================================
                # 7. VALIDATE MANAGER SELECTIONS
                # =====================================

                st.subheader("7. Validate and Confirm Selection")

                if st.button(
                    "Validate and Confirm Manager Selection",
                    type="primary",
                    use_container_width=True
                ):

                    selected_records = []

                    for employee_id, group in employee_groups:

                        employee_row = group.iloc[0]

                        selected_label = st.session_state.get(
                            f"manager_station_{employee_id}",
                            "-- Not selected --"
                        )

                        if selected_label == "-- Not selected --":
                            continue

                        selected_station_id = (
                            selected_label.split(" - ")[0]
                        )

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

                    selection_df = pd.DataFrame(
                        selected_records
                    )

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
                                selected_employees=(
                                    "employee_id",
                                    "count"
                                ),
                                station_capacity=(
                                    "station_capacity",
                                    "min"
                                )
                            )
                        )

                        for _, row in capacity_usage.iterrows():

                            if (
                                row["selected_employees"]
                                > row["station_capacity"]
                            ):

                                validation_errors.append(
                                    f'{row["station_id"]} '
                                    f'({row["shift"]} Shift): '
                                    f'{row["selected_employees"]} employees '
                                    f'selected, but capacity is '
                                    f'{row["station_capacity"]}.'
                                )

                    if validation_errors:

                        st.session_state.pop(
                            "confirmed_manager_selection",
                            None
                        )

                        st.error(
                            "Manager selection validation failed."
                        )

                        for error in validation_errors:
                            st.warning(error)

                    else:

                        st.session_state[
                            "confirmed_manager_selection"
                        ] = selection_df.copy()

                        st.success(
                            "Manager selection passed validation!"
                        )

                # =====================================
                # 8. DISPLAY CONFIRMED SELECTION
                # =====================================

                if "confirmed_manager_selection" in st.session_state:

                    st.divider()

                    st.markdown(
                        "### Confirmed Proposed Station Assignments"
                    )

                    confirmed_df = st.session_state[
                        "confirmed_manager_selection"
                    ]

                    st.dataframe(
                        confirmed_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.metric(
                        "Employees Selected",
                        len(confirmed_df)
                    )

                    confirmed_csv = confirmed_df.to_csv(
                        index=False
                    )

                    st.download_button(
                        "Download Manager Selection",
                        data=confirmed_csv,
                        file_name="manager_station_selection.csv",
                        mime="text/csv"
                    )

                    st.success(
                        "The proposed selections have passed "
                        "employee and station capacity validation."
                    )

                    st.caption(
                        "These are confirmed proposals in the current "
                        "Streamlit session. They have not been written "
                        "to the existing allocation CSV files."
                    )


# =====================================================
# 9. WORKFORCE ANALYTICS DASHBOARD
# =====================================================

st.divider()

st.subheader("8. Workforce Analytics Dashboard")

if (
    all_data_valid
    and "uploaded_recommendations" in st.session_state
):

    show_analytics = st.checkbox(
        "Show Workforce Analytics Dashboard",
        value=False,
        key="show_workforce_analytics"
    )

    if show_analytics:

        confirmed_selection = st.session_state.get(
            "confirmed_manager_selection"
        )

        if confirmed_selection is None:
            confirmed_selection = pd.DataFrame()

        try:

            show_workforce_analytics(
                employees_df=employee_df,
                recommendations_df=st.session_state[
                    "uploaded_recommendations"
                ],
                manager_selection_df=confirmed_selection
            )

        except Exception as error:

            st.error(
                f"Unable to display workforce analytics: {error}"
            )

else:

    st.info(
        "Upload and validate all three datasets, then generate "
        "station recommendations to access workforce analytics."
    )


# =====================================================
# 10. DATA SAFETY NOTICE
# =====================================================

st.divider()

st.caption(
    "Data safety: uploaded datasets are processed in memory. "
    "Manager selections remain in the current Streamlit session "
    "and can be downloaded. Existing employee, skill, attendance "
    "and allocation CSV files are not modified."
)
# =====================================================
# 9. EMPLOYEE SKILL GAP ANALYSIS
# =====================================================


st.divider()

st.subheader("🎯 Employee Skill Gap Analysis")

show_skill_gap = st.checkbox(
    "Show Employee Skill Gap Dashboard",
    key="show_skill_gap_dashboard"
)

if show_skill_gap:

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

            st.error(
                f"Unable to display skill gap analytics: {error}"
            )

    else:

        st.warning(
            "Please upload and validate employee and skill files first."
        )