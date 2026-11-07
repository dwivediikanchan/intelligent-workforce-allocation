
import streamlit as st
import pandas as pd

from datetime import date

from streamlit_sortables import sort_items

from database_repository import (
    get_employees,
    get_allocations,
    get_attendance,
    get_stations,
    get_allocation_audit,
    get_defect_records
)


# =====================================================
# LOAD POSTGRESQL DATA
# =====================================================

@st.cache_data(ttl=10)
def load_manager_data(allocation_date):

    employees = get_employees()
    allocations = get_allocations()
    attendance = get_attendance()
    stations = get_stations()
    audit = get_allocation_audit()
    defects = get_defect_records()

    selected_date = str(allocation_date)

    # Filter allocations for selected date

    allocations = allocations[
        allocations["allocation_date"].astype(str)
        == selected_date
    ].copy()

    allocations = allocations[
        allocations["status"].astype(str).str.strip()
        == "Allocated"
    ].copy()

    # Attach employee names

    if not allocations.empty:

        allocations = allocations.merge(
            employees[["employee_id", "employee_name"]],
            on="employee_id",
            how="left"
        )

    else:

        allocations["employee_name"] = pd.Series(dtype="object")

    # Include unallocated active employees

    active_employees = employees[
        employees["status"].astype(str).str.strip()
        == "Active"
    ].copy()

    allocated_ids = set(
        allocations["employee_id"].astype(str)
    )

    unallocated = active_employees[
        ~active_employees["employee_id"].astype(str).isin(
            allocated_ids
        )
    ].copy()

    attendance_today = attendance[
        attendance["attendance_date"].astype(str)
        == selected_date
    ][["employee_id", "attendance_status"]].copy()

    if not unallocated.empty:

        unallocated = unallocated.merge(
            attendance_today,
            on="employee_id",
            how="left"
        )

        unallocated["station_id"] = "Not Assigned"
        unallocated["skill_score"] = 0
        unallocated["allocation_date"] = selected_date

        unallocated["status"] = (
            unallocated["attendance_status"]
            .fillna("Attendance Missing")
        )

        unallocated = unallocated[
            [
                "employee_id",
                "employee_name",
                "station_id",
                "allocation_date",
                "shift",
                "skill_score",
                "status"
            ]
        ]

        allocations = pd.concat(
            [allocations, unallocated],
            ignore_index=True
        )

    return (
        employees,
        allocations,
        attendance,
        stations,
        audit,
        defects
    )


# =====================================================
# MAIN MANAGER DASHBOARD
# =====================================================

def show_manager_dashboard():

    st.title("🏭 Manager Dashboard")

    st.caption(
        "Employee allocation monitoring, "
        "station management and manager-controlled reassignment."
    )

    st.divider()

    # -------------------------------------------------
    # DATE CONFIGURATION
    # -------------------------------------------------

    st.subheader("Dashboard Configuration")

    selected_date = st.date_input(
        "Select Allocation Date",
        value=date(2026, 11, 4),
        key="manager_allocation_date"
    )

    allocation_date = selected_date.isoformat()

    # -------------------------------------------------
    # SESSION STATE
    # -------------------------------------------------

    defaults = {
        "manager_proposed_moves": [],
        "manager_board_state": None,
        "manager_board_shift": None,
        "manager_board_date": None,
        "manager_board_version": 0,
        "manager_previous_shift": None,
        "manager_approval_result": None
    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value

    # -------------------------------------------------
    # LOAD DATA
    # -------------------------------------------------

    try:

        (
            employees,
            allocations,
            attendance,
            stations,
            audit,
            defects
        ) = load_manager_data(allocation_date)

    except Exception as error:

        st.error(f"Unable to load manager dashboard: {error}")
        return

    # -------------------------------------------------
    # SYSTEM OVERVIEW
    # -------------------------------------------------

    st.subheader("📊 System Data Overview")

    active_employees = employees[
        employees["status"].astype(str).str.strip()
        == "Active"
    ]

    allocated = allocations[
        allocations["status"].astype(str).str.strip()
        == "Allocated"
    ]

    total_defects = (
        int(pd.to_numeric(
            defects["defect_count"], errors="coerce"
        ).fillna(0).sum())
        if not defects.empty
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Employees",
        len(employees)
    )

    col2.metric(
        "Active Employees",
        len(active_employees)
    )

    col3.metric(
        "Allocated Employees",
        len(allocated)
    )

    col4.metric(
        "Total Stations",
        len(stations)
    )

    st.caption(f"Total recorded defects: {total_defects}")

    # -------------------------------------------------
    # CURRENT ALLOCATIONS
    # -------------------------------------------------

    st.divider()

    st.subheader("👥 Current Employee Allocations")

    st.dataframe(
        allocations,
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------------------------
    # SHIFT SELECTION
    # -------------------------------------------------

    st.divider()

    st.header("🧩 Interactive Station Allocation Board")

    selected_shift = st.selectbox(
        "Select Shift",
        ["Morning", "Evening", "Night"],
        key="manager_selected_shift"
    )

    # Reset pending moves when date or shift changes

    if (
        st.session_state["manager_previous_shift"]
        != selected_shift
        or st.session_state["manager_board_date"]
        != allocation_date
    ):

        st.session_state["manager_proposed_moves"] = []
        st.session_state["manager_board_state"] = None
        st.session_state["manager_board_version"] += 1

    st.session_state["manager_previous_shift"] = selected_shift

    st.session_state["manager_board_date"] = allocation_date

    # -------------------------------------------------
    # FILTER SHIFT ALLOCATIONS
    # -------------------------------------------------

    shift_allocations = allocated[
        allocated["shift"].astype(str).str.strip()
        == selected_shift
    ].copy()

    original_allocations = dict(
        zip(
            shift_allocations["employee_id"].astype(str),
            shift_allocations["station_id"].astype(str)
        )
    )

    # -------------------------------------------------
    # BUILD STATION BOARD
    # -------------------------------------------------

    def build_station_board():

        containers = []

        for _, station in stations.iterrows():

            station_id = str(station["station_id"])
            station_name = str(station["station_name"])
            capacity = int(station["capacity"])

            station_employees = shift_allocations[
                shift_allocations["station_id"].astype(str)
                == station_id
            ]

            employee_cards = []

            for _, employee in station_employees.iterrows():

                score = employee.get("skill_score", 0)

                employee_cards.append(
                    f"{employee['employee_id']} — "
                    f"{employee['employee_name']} "
                    f"(Score: {score})"
                )

            containers.append({
                "header": (
                    f"{station_id} - {station_name} "
                    f"({len(employee_cards)}/{capacity})"
                ),
                "items": employee_cards
            })

        return containers

    # -------------------------------------------------
    # INITIALIZE BOARD
    # -------------------------------------------------

    if (
        st.session_state["manager_board_state"] is None
        or st.session_state["manager_board_shift"] != selected_shift
    ):

        st.session_state["manager_board_state"] = (
            build_station_board()
        )

        st.session_state["manager_board_shift"] = selected_shift

    # -------------------------------------------------
    # DISPLAY DRAG AND DROP BOARD
    # -------------------------------------------------

    st.caption(
        "Drag employee cards between stations to preview "
        "allocation changes. Changes are not saved until approved."
    )

    sorted_containers = sort_items(
        st.session_state["manager_board_state"],
        multi_containers=True,
        key=(
            f"manager_board_{allocation_date}_"
            f"{selected_shift}_"
            f"{st.session_state['manager_board_version']}"
        )
    )

    if isinstance(sorted_containers, list):

        st.session_state["manager_board_state"] = sorted_containers

    board = st.session_state["manager_board_state"]

    # -------------------------------------------------
    # DETECT PROPOSED MOVEMENTS
    # -------------------------------------------------

    detected_moves = []

    valid_board = True
    seen_employees = set()

    if not isinstance(board, list):

        valid_board = False

        st.error("Unexpected drag-and-drop board format.")

    else:

        for container in board:

            if not isinstance(container, dict):

                valid_board = False
                st.error("Invalid station container.")
                break

            header = str(container.get("header", ""))

            target_station_id = next(
                (
                    str(station_id)
                    for station_id in stations["station_id"]
                    if header.startswith(f"{station_id} - ")
                ),
                None
            )

            if target_station_id is None:

                valid_board = False
                st.error(f"Unable to identify station: {header}")
                break

            for employee_card in container.get("items", []):

                employee_id = (
                    str(employee_card)
                    .split(" — ", 1)[0]
                    .strip()
                )

                if employee_id not in original_allocations:

                    valid_board = False
                    st.error(f"Unknown employee ID: {employee_id}")
                    break

                if employee_id in seen_employees:

                    valid_board = False
                    st.error(
                        f"Duplicate employee detected: {employee_id}"
                    )
                    break

                seen_employees.add(employee_id)

                original_station_id = original_allocations[
                    employee_id
                ]

                if original_station_id != target_station_id:

                    detected_moves.append({
                        "employee_id": employee_id,
                        "employee_name": str(employee_card),
                        "old_station": original_station_id,
                        "new_station": target_station_id
                    })

            if not valid_board:
                break

    # Verify no employee card disappeared

    if valid_board:

        missing_employees = (
            set(original_allocations.keys()) - seen_employees
        )

        if missing_employees:

            valid_board = False

            st.error(
                "Employee cards missing from board: "
                + ", ".join(sorted(missing_employees))
            )

    # Preserve proposed movements

    if valid_board:

        st.session_state["manager_proposed_moves"] = (
            detected_moves.copy()
        )

    else:

        st.error(
            "Board validation failed. "
            "Pending movements have not been approved."
        )

    proposed_moves = st.session_state["manager_proposed_moves"]

    # -------------------------------------------------
    # PROPOSED CHANGES
    # -------------------------------------------------

    st.divider()

    st.subheader("🔄 Proposed Allocation Changes")

    if proposed_moves:

        st.warning(
            f"{len(proposed_moves)} proposed movement(s) pending approval."
        )

        st.dataframe(
            pd.DataFrame(proposed_moves),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success("No allocation changes detected.")

    # -------------------------------------------------
    # MANAGER APPROVAL
    # -------------------------------------------------

    st.divider()

    st.subheader("🔐 Manager Approval")

    if proposed_moves:

        if len(proposed_moves) > 1:

            st.info(
                "Only one movement can be approved at a time. "
                "Approve one movement before proposing another."
            )

        with st.form("manager_approval_form"):

            manager_id = st.text_input(
                "Enter Manager ID",
                value="Manager01"
            )

            confirm_changes = st.checkbox(
                "I have reviewed and approve this allocation change."
            )

            submitted = st.form_submit_button(
                "Confirm and Save Allocation Change",
                type="primary",
                disabled=(len(proposed_moves) != 1)
            )

        st.warning(
            "Approving a change updates PostgreSQL allocations "
            "and writes an audit record."
        )

        if submitted:

            if not manager_id.strip():

                st.error("Manager ID cannot be empty.")

            elif not confirm_changes:

                st.error("Please confirm the allocation change.")

            else:

                from database_reassignment import (
                    reassign_employee_db
                )

                move = proposed_moves[0]

                try:

                    result = reassign_employee_db(
                        employee_id=move["employee_id"],
                        new_station_id=move["new_station"],
                        manager_id=manager_id.strip(),
                        allocation_date=allocation_date
                    )

                    if result:

                        st.session_state["manager_approval_result"] = {
                            "employee_id": move["employee_id"],
                            "old_station": move["old_station"],
                            "new_station": move["new_station"],
                            "manager_id": manager_id.strip(),
                            "allocation_date": allocation_date
                        }

                        st.session_state["manager_proposed_moves"] = []
                        st.session_state["manager_board_state"] = None

                        load_manager_data.clear()

                        st.success(
                            "Allocation successfully saved to PostgreSQL."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Backend validation rejected the change. "
                            "The allocation was not saved."
                        )

                except Exception as error:

                    st.error(
                        f"Unable to save allocation: {error}"
                    )

    # -------------------------------------------------
    # DISCARD CHANGES
    # -------------------------------------------------

    if st.button("Discard Proposed Changes"):

        st.session_state["manager_proposed_moves"] = []
        st.session_state["manager_board_state"] = None
        st.session_state["manager_board_version"] += 1

        st.rerun()

    # -------------------------------------------------
    # LAST APPROVAL
    # -------------------------------------------------

    approval = st.session_state["manager_approval_result"]

    if approval:

        st.divider()

        st.subheader("✅ Last Successful Manager Approval")

        col1, col2 = st.columns(2)

        with col1:

            st.write(f"**Employee:** {approval['employee_id']}")
            st.write(f"**Previous Station:** {approval['old_station']}")
            st.write(f"**New Station:** {approval['new_station']}")

        with col2:

            st.write(f"**Approved By:** {approval['manager_id']}")
            st.write(f"**Allocation Date:** {approval['allocation_date']}")

        if st.button("Dismiss Approval Confirmation"):

            st.session_state["manager_approval_result"] = None
            st.rerun()

    # -------------------------------------------------
    # AUDIT HISTORY
    # -------------------------------------------------

    st.divider()

    st.subheader("📋 Manager Allocation Audit History")

    if not audit.empty:

        audit_display = audit.sort_values(
            "id",
            ascending=False
        )

        st.dataframe(
            audit_display,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No manager allocation audit history available.")
