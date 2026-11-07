
import streamlit as st
import pandas as pd

from database_repository import get_allocation_audit


def show_allocation_history():

    st.title("📜 Allocation History")

    st.caption(
        "PostgreSQL-powered allocation tracking, "
        "manager actions and reassignment audit history."
    )

    # ---------------------------------
    # LOAD POSTGRESQL AUDIT DATA
    # ---------------------------------

    try:
        history = get_allocation_audit()

    except Exception as error:
        st.error(f"Unable to load allocation history: {error}")
        return

    if history.empty:
        st.info("No allocation history available in PostgreSQL.")
        return

    required_columns = [
        "timestamp",
        "manager_id",
        "employee_id",
        "shift",
        "old_station_id",
        "new_station_id",
        "skill_score",
        "action",
        "allocation_date"
    ]

    missing_columns = [
        column for column in required_columns
        if column not in history.columns
    ]

    if missing_columns:
        st.error(f"Missing audit columns: {missing_columns}")
        return

    history = history.copy()

    history["timestamp"] = pd.to_datetime(
        history["timestamp"], errors="coerce"
    )

    history["allocation_date"] = pd.to_datetime(
        history["allocation_date"], errors="coerce"
    ).dt.date

    # ---------------------------------
    # FILTERS
    # ---------------------------------

    st.subheader("Filter Allocation History")

    col1, col2, col3 = st.columns(3)

    employee_options = ["All Employees"] + sorted(
        history["employee_id"].dropna().astype(str).unique().tolist()
    )

    manager_options = ["All Managers"] + sorted(
        history["manager_id"].dropna().astype(str).unique().tolist()
    )

    date_options = sorted(
        history["allocation_date"].dropna().unique().tolist(),
        reverse=True
    )

    with col1:
        selected_employee = st.selectbox(
            "Employee",
            employee_options
        )

    with col2:
        selected_manager = st.selectbox(
            "Manager",
            manager_options
        )

    with col3:
        selected_date = st.selectbox(
            "Allocation Date",
            ["All Dates"] + date_options
        )

    filtered = history.copy()

    if selected_employee != "All Employees":
        filtered = filtered[
            filtered["employee_id"].astype(str) == selected_employee
        ]

    if selected_manager != "All Managers":
        filtered = filtered[
            filtered["manager_id"].astype(str) == selected_manager
        ]

    if selected_date != "All Dates":
        filtered = filtered[
            filtered["allocation_date"] == selected_date
        ]

    filtered = filtered.sort_values(
        "timestamp",
        ascending=False
    )

    # ---------------------------------
    # KPI METRICS
    # ---------------------------------

    st.divider()
    st.subheader("Allocation Audit Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Audit Records", len(history))
    col2.metric("Filtered Records", len(filtered))
    col3.metric(
        "Employees Involved",
        filtered["employee_id"].nunique()
    )
    col4.metric(
        "Managers Involved",
        filtered["manager_id"].nunique()
    )

    # ---------------------------------
    # HISTORY TABLE
    # ---------------------------------

    st.divider()
    st.subheader("Manager Allocation History")

    if filtered.empty:
        st.warning("No matching allocation history found.")

    else:
        st.dataframe(
            filtered[required_columns],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Allocation History",
            filtered[required_columns].to_csv(index=False),
            "allocation_history_report.csv",
            "text/csv"
        )

    st.caption(
        "Records are retrieved directly from PostgreSQL. "
        "This page does not modify allocation or audit records."
    )
