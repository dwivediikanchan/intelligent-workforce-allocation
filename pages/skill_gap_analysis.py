
import streamlit as st

from database_repository import (
    get_employees,
    get_employee_skills
)

from skill_gap_analytics import show_skill_gap_analytics


def show_skill_gap_analysis_page():

    st.caption(
        "PostgreSQL-powered employee training gaps, "
        "skill verification and station requirement analysis."
    )

    try:
        employees_df = get_employees()
        skills_df = get_employee_skills()

    except Exception as error:
        st.error(f"Unable to load workforce data: {error}")
        return

    if employees_df.empty:
        st.warning("No employee records found in PostgreSQL.")
        return

    if skills_df.empty:
        st.warning("No employee skill records found in PostgreSQL.")
        return

    st.subheader("PostgreSQL Data Availability")

    col1, col2 = st.columns(2)

    col1.metric("Employees", len(employees_df))
    col2.metric("Employee Skill Records", len(skills_df))

    st.divider()

    show_skill_gap_analytics(
        employees_df,
        skills_df
    )
