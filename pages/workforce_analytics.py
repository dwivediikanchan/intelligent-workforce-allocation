
import streamlit as st
import pandas as pd
from datetime import date

from database_repository import (
    get_employees,
    get_employee_skills,
    get_attendance,
    get_allocations,
    get_stations
)

from uploaded_station_recommendation import (
    generate_uploaded_station_recommendations
)

from workforce_analytics import show_workforce_analytics


def show_workforce_analytics_page():

    st.title("📊 Workforce Analytics")

    st.caption(
        "PostgreSQL-powered workforce intelligence, "
        "skill eligibility and station recommendation analytics."
    )

    st.divider()

    # =========================================
    # 1. SELECT ANALYSIS DATE
    # =========================================

    selected_date = st.date_input(
        "Select Workforce Analysis Date",
        value=date(2026, 11, 4),
        key="analytics_recommendation_date"
    )

    recommendation_date = selected_date.isoformat()

    # =========================================
    # 2. LOAD POSTGRESQL DATA
    # =========================================

    try:

        employees = get_employees()
        skills = get_employee_skills()
        attendance = get_attendance()
        allocations = get_allocations()
        stations = get_stations()

    except Exception as error:

        st.error(
            f"Unable to load workforce data from PostgreSQL: {error}"
        )
        return

    if employees.empty:

        st.warning("No employee records found in PostgreSQL.")
        return

    if stations.empty:

        st.warning("No station records found in PostgreSQL.")
        return

    # =========================================
    # 3. DATA AVAILABILITY
    # =========================================

    st.subheader("PostgreSQL Data Availability")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Employees", len(employees))
    col2.metric("Employee Skills", len(skills))
    col3.metric("Attendance Records", len(attendance))
    col4.metric("Stations", len(stations))

    st.divider()

    # =========================================
    # 4. GENERATE RECOMMENDATIONS
    # =========================================

    st.subheader("Generate Skill-Based Recommendations")

    st.info(
        "Recommendations use active employees, verified skills, "
        "daily attendance and PostgreSQL station requirements. "
        "This is an analytical preview, not an actual allocation."
    )

    if st.button(
        "Generate Workforce Analytics",
        type="primary"
    ):

        try:

            with st.spinner(
                "Generating station recommendations..."
            ):

                recommendations = (
                    generate_uploaded_station_recommendations(
                        employees_df=employees,
                        skills_df=skills,
                        attendance_df=attendance,
                        recommendation_date=recommendation_date
                    )
                )

                # Manager selections from saved PostgreSQL allocations

                selected_allocations = allocations.copy()

                if not selected_allocations.empty:

                    selected_allocations = (
                        selected_allocations[
                            selected_allocations[
                                "allocation_date"
                            ].astype(str) == recommendation_date
                        ].copy()
                    )

                    selected_allocations = selected_allocations[
                        selected_allocations["status"].astype(str)
                        .str.strip().eq("Allocated")
                    ]

                    selected_allocations = (
                        selected_allocations.merge(
                            employees[
                                ["employee_id", "employee_name"]
                            ],
                            on="employee_id",
                            how="left"
                        )
                    )

                    selected_allocations = (
                        selected_allocations.merge(
                            stations[
                                ["station_id", "station_name"]
                            ],
                            on="station_id",
                            how="left"
                        )
                    )

                    manager_selection = selected_allocations[
                        [
                            "employee_id",
                            "employee_name",
                            "station_id",
                            "station_name",
                            "shift"
                        ]
                    ].copy()

                else:

                    manager_selection = pd.DataFrame(
                        columns=[
                            "employee_id",
                            "employee_name",
                            "station_id",
                            "station_name",
                            "shift"
                        ]
                    )

                # Save results in Streamlit session

                st.session_state[
                    "workforce_analytics_recommendations"
                ] = recommendations

                st.session_state[
                    "workforce_analytics_manager_selection"
                ] = manager_selection

                st.session_state[
                    "workforce_analytics_date"
                ] = recommendation_date

                st.success(
                    "Workforce recommendations generated successfully."
                )

        except Exception as error:

            st.error(
                f"Unable to generate workforce recommendations: {error}"
            )

            return

    # =========================================
    # 5. DISPLAY ANALYTICS
    # =========================================

    stored_date = st.session_state.get(
        "workforce_analytics_date"
    )

    if stored_date == recommendation_date:

        recommendations = st.session_state.get(
            "workforce_analytics_recommendations"
        )

        manager_selection = st.session_state.get(
            "workforce_analytics_manager_selection"
        )

        if isinstance(recommendations, pd.DataFrame):

            st.divider()

            st.subheader(
                f"Workforce Analytics Report — {recommendation_date}"
            )

            if recommendations.empty:

                st.warning(
                    "No recommendation records were generated "
                    "for the selected date."
                )

            else:

                # Preserve existing analytics implementation

                show_workforce_analytics(
                    employees_df=employees,
                    recommendations_df=recommendations,
                    manager_selection_df=manager_selection
                )

                # Detailed recommendation table

                st.divider()

                st.subheader("Complete Station Recommendation Details")

                st.dataframe(
                    recommendations,
                    use_container_width=True,
                    hide_index=True
                )

    elif stored_date is not None:

        st.info(
            "The selected date has changed. "
            "Generate analytics again for this date."
        )

    else:

        st.info(
            "Select a date and click Generate Workforce Analytics "
            "to view the dashboard."
        )
