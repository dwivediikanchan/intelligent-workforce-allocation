
import streamlit as st
import pandas as pd

from datetime import date, time

from database_connection import SessionLocal
from database_models import Attendance
from database_repository import get_employees, get_attendance


def show_attendance_management():

    st.title("📅 Attendance Management")
    st.caption("Record, update and review employee attendance using PostgreSQL.")

    employees = get_employees()

    if employees.empty:
        st.warning("No employee records found.")
        return

    active_employees = employees[
        employees["status"] == "Active"
    ].copy()

    if active_employees.empty:
        st.warning("No active employees are available.")
        return

    employee_options = {
        f"{row.employee_id} - {row.employee_name}": row.employee_id
        for row in active_employees.itertuples()
    }

    tab1, tab2 = st.tabs([
        "Record / Update Attendance",
        "Attendance Records"
    ])

    # -----------------------------------------
    # TAB 1: RECORD OR UPDATE ATTENDANCE
    # -----------------------------------------

    with tab1:

        st.subheader("Daily Attendance Entry")

        with st.form("attendance_form"):

            selected_employee = st.selectbox(
                "Employee",
                options=list(employee_options.keys())
            )

            selected_date = st.date_input(
                "Attendance Date",
                value=date.today()
            )

            selected_shift = st.selectbox(
                "Shift",
                ["Morning", "Evening", "Night"]
            )

            attendance_status = st.selectbox(
                "Attendance Status",
                ["Present", "Absent", "Leave"]
            )

            col1, col2 = st.columns(2)

            with col1:
                check_in = st.time_input(
                    "Check-in Time",
                    value=time(8, 0)
                )

            with col2:
                check_out = st.time_input(
                    "Check-out Time",
                    value=time(17, 0)
                )

            submitted = st.form_submit_button(
                "Save Attendance",
                use_container_width=True
            )

        if submitted:

            employee_id = employee_options[selected_employee]

            if attendance_status == "Present" and check_in == check_out:
                st.error("Check-in and check-out times cannot be identical.")

            else:

                db = SessionLocal()

                try:

                    existing_record = db.query(Attendance).filter_by(
                        employee_id=employee_id,
                        attendance_date=selected_date
                    ).first()

                    if existing_record:

                        existing_record.shift = selected_shift
                        existing_record.attendance_status = attendance_status

                        existing_record.check_in = (
                            check_in if attendance_status == "Present" else None
                        )

                        existing_record.check_out = (
                            check_out if attendance_status == "Present" else None
                        )

                        message = "Attendance updated successfully."

                    else:

                        new_record = Attendance(
                            employee_id=employee_id,
                            attendance_date=selected_date,
                            shift=selected_shift,
                            attendance_status=attendance_status,
                            check_in=(
                                check_in if attendance_status == "Present" else None
                            ),
                            check_out=(
                                check_out if attendance_status == "Present" else None
                            )
                        )

                        db.add(new_record)
                        message = "Attendance recorded successfully."

                    db.commit()
                    st.success(message)

                except Exception as error:

                    db.rollback()
                    st.error(f"Attendance could not be saved: {error}")

                finally:
                    db.close()

    # -----------------------------------------
    # TAB 2: VIEW ATTENDANCE RECORDS
    # -----------------------------------------

    with tab2:

        st.subheader("Attendance Register")

        attendance = get_attendance()

        if attendance.empty:
            st.info("No attendance records found.")

        else:

            attendance["attendance_date"] = pd.to_datetime(
                attendance["attendance_date"]
            ).dt.date

            report_date = st.date_input(
                "Filter by Date",
                value=date.today(),
                key="attendance_report_date"
            )

            filtered = attendance[
                attendance["attendance_date"] == report_date
            ].copy()

            if filtered.empty:
                st.info("No attendance records for the selected date.")

            else:

                present = (
                    filtered["attendance_status"] == "Present"
                ).sum()

                absent = (
                    filtered["attendance_status"] == "Absent"
                ).sum()

                leave = (
                    filtered["attendance_status"] == "Leave"
                ).sum()

                col1, col2, col3 = st.columns(3)

                col1.metric("Present", int(present))
                col2.metric("Absent", int(absent))
                col3.metric("On Leave", int(leave))

                filtered = filtered.merge(
                    employees[["employee_id", "employee_name"]],
                    on="employee_id",
                    how="left"
                )

                st.dataframe(
                    filtered[
                        [
                            "employee_id",
                            "employee_name",
                            "attendance_date",
                            "shift",
                            "attendance_status",
                            "check_in",
                            "check_out"
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True
                )
