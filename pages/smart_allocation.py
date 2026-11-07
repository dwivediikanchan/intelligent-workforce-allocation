
import streamlit as st
import pandas as pd

from datetime import date

from daily_allocation_engine import run_daily_allocation
from allocation_validator import validate_allocation_preview


def show_smart_allocation():

    st.title("⚙️ Smart Allocation")

    st.caption(
        "Attendance-aware employee-to-station allocation "
        "with verified skill matching and capacity validation."
    )

    st.divider()

    # ==========================================
    # DAILY ALLOCATION CONFIGURATION
    # ==========================================

    st.subheader("Daily Allocation Configuration")

    selected_date = st.date_input(
        "Select Allocation Date",
        value=date.today(),
        key="smart_allocation_date"
    )

    st.info(
        "Only active employees with Present attendance "
        "and matching shifts will be considered."
    )

    # ==========================================
    # GENERATE ALLOCATION
    # ==========================================

    if st.button(
        "🚀 Generate Daily Allocation",
        type="primary",
        use_container_width=True
    ):

        try:

            with st.spinner("Generating allocation preview..."):

                results = run_daily_allocation(
                    selected_date=selected_date
                )

            st.session_state["daily_allocation_results"] = results
            st.session_state["daily_allocation_date"] = selected_date

            # Run validation on the generated preview

            with st.spinner("Validating allocation preview..."):

                validation = validate_allocation_preview(
                    preview=results,
                    allocation_date=selected_date
                )

            st.session_state["allocation_validation"] = validation

            st.success("Allocation preview generated and validation completed.")

        except Exception as error:

            st.error(f"Allocation process failed: {error}")

            st.session_state.pop("daily_allocation_results", None)
            st.session_state.pop("allocation_validation", None)

    # ==========================================
    # DISPLAY ALLOCATION RESULTS
    # ==========================================

    if "daily_allocation_results" in st.session_state:

        results = st.session_state["daily_allocation_results"]

        saved_date = st.session_state["daily_allocation_date"]

        if saved_date != selected_date:

            st.info(
                "The displayed results belong to another date. "
                "Generate allocation again for the selected date."
            )

        else:

            st.divider()

            st.subheader("Allocation Results")

            if results.empty:

                st.warning("No allocation records generated.")

            else:

                total = len(results)

                allocated = (
                    results["status"].astype(str).str.strip()
                    == "Allocated"
                ).sum()

                needs_attention = total - allocated

                col1, col2, col3 = st.columns(3)

                col1.metric("Total Employees", int(total))
                col2.metric("Allocated", int(allocated))
                col3.metric("Needs Attention", int(needs_attention))

                st.dataframe(
                    results,
                    use_container_width=True,
                    hide_index=True
                )

                # STATION-WISE SUMMARY

                st.subheader("Station-wise Allocation")

                allocated_data = results[
                    results["status"].astype(str).str.strip()
                    == "Allocated"
                ]

                if allocated_data.empty:

                    st.info("No successful allocations to summarize.")

                else:

                    utilization = (
                        allocated_data.groupby(
                            ["station_id", "shift"]
                        )
                        .size()
                        .reset_index(
                            name="allocated_employees"
                        )
                    )

                    st.dataframe(
                        utilization,
                        use_container_width=True,
                        hide_index=True
                    )

                # DOWNLOAD PREVIEW

                csv_data = results.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    "⬇️ Download Allocation Preview",
                    data=csv_data,
                    file_name=f"daily_allocation_{selected_date}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                st.warning(
                    "This is a preview only. PostgreSQL allocation "
                    "records have not been modified."
                )

    # ==========================================
    # PREVIEW VALIDATION RESULTS
    # ==========================================

    st.divider()

    st.subheader("Allocation Validation")

    if (
        "allocation_validation" in st.session_state
        and st.session_state.get("daily_allocation_date") == selected_date
    ):

        validation = st.session_state["allocation_validation"]

        if validation["passed"]:

            st.success("All allocation preview validations passed.")

        else:

            st.error("Allocation preview validation failed.")

            for error in validation["errors"]:
                st.write(f"- {error}")

        summary = validation.get("summary", {})

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Duplicate Assignments",
            summary.get("duplicates", 0)
        )

        col2.metric(
            "Capacity Violations",
            summary.get("capacity_violations", 0)
        )

        col3.metric(
            "Skill Violations",
            summary.get("skill_violations", 0)
        )

        st.subheader("Capacity Validation Report")

        st.dataframe(
            validation["capacity_report"],
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Skill Eligibility Report")

        st.dataframe(
            validation["skill_report"],
            use_container_width=True,
            hide_index=True
        )

        if not validation["conflict_report"].empty:

            st.subheader("Multiple Station Conflicts")

            st.dataframe(
                validation["conflict_report"],
                use_container_width=True
            )

        if not validation["duplicate_report"].empty:

            st.subheader("Duplicate Assignments")

            st.dataframe(
                validation["duplicate_report"],
                use_container_width=True,
                hide_index=True
            )

        st.caption(
            "Validation reads PostgreSQL master data. "
            "It does not modify PostgreSQL allocation records."
        )

    else:

        st.info(
            "Generate an allocation preview to run and display "
            "the validation checks."
        )
