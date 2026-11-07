
import streamlit as st
import pandas as pd
from pathlib import Path
from streamlit_sortables import sort_items

from database_repository import (
    get_employees,
    get_allocations,
    get_attendance,
    get_stations,
    get_allocation_audit,
    get_defect_records
)


# -------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------

st.set_page_config(
    page_title="Smart Workforce Manager Dashboard",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Smart Workforce Allocation System")
st.caption("Intelligent Employee Allocation and Station Management")


# -------------------------------------------------
# FILE PATHS
# -------------------------------------------------


ALLOCATION_DATE = "2026-11-04"


# -------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------

defaults = {
    "proposed_moves": [],
    "pending_shift": None,
    "board_version": 0,
    "board_state": None,
    "board_state_shift": None,
    "board_state_version": None,
    "previous_shift": None,
    "approval_result": None
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# -------------------------------------------------
# LOAD DATA FROM POSTGRESQL
# -------------------------------------------------

@st.cache_data
def load_data():

    employees = get_employees()

    raw_allocations = get_allocations()

    attendance = get_attendance()

    stations = get_stations()

    audit = get_allocation_audit()

    # Load defects from CSV for now.
    # Load defects from PostgreSQL.
    defects = get_defect_records()
    
    # Filter allocations for the dashboard date.
    raw_allocations = raw_allocations[
        raw_allocations["allocation_date"].astype(str)
        == ALLOCATION_DATE
    ].copy()

    # Attach employee names to allocation records.
    allocations = raw_allocations.merge(
        employees[["employee_id", "employee_name"]],
        on="employee_id",
        how="left"
    )

    # Include employees who do not have an allocation.
    allocated_ids = set(
        allocations["employee_id"].astype(str)
    )

    unallocated_employees = employees[
        ~employees["employee_id"].astype(str).isin(allocated_ids)
    ].copy()

    if not unallocated_employees.empty:

        attendance_today = attendance[
            attendance["attendance_date"].astype(str)
            == ALLOCATION_DATE
        ][["employee_id", "attendance_status"]]

        unallocated_employees = unallocated_employees.merge(
            attendance_today,
            on="employee_id",
            how="left"
        )

        unallocated_employees["station_id"] = "Not Assigned"
        unallocated_employees["skill_score"] = 0

        unallocated_employees["status"] = (
            unallocated_employees["attendance_status"]
            .fillna("Not Assigned")
        )

        unallocated_employees["allocation_date"] = ALLOCATION_DATE

        unallocated_employees = unallocated_employees[
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
            [
                allocations,
                unallocated_employees
            ],
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


try:

    (
        employees,
        allocations,
        attendance,
        stations,
        audit,
        defects
    ) = load_data()

except Exception as error:

    st.error(f"Unable to load dashboard data: {error}")
    st.stop()


# -------------------------------------------------
# SYSTEM DATA OVERVIEW
# -------------------------------------------------

st.subheader("📊 System Data Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Employees", len(employees))

with col2:
    st.metric(
        "Active Employees",
        len(employees[employees["status"] == "Active"])
    )

with col3:
    st.metric(
        "Allocated Employees",
        len(allocations[allocations["status"] == "Allocated"])
    )

with col4:
    st.metric("Total Stations", len(stations))


# -------------------------------------------------
# CURRENT EMPLOYEE ALLOCATIONS
# -------------------------------------------------

st.divider()

st.subheader("👥 Current Employee Allocations")

st.dataframe(
    allocations,
    width="stretch",
    hide_index=True
)


# -------------------------------------------------
# DRAG AND DROP STATION ALLOCATION BOARD
# -------------------------------------------------

st.divider()

st.header("🧩 Interactive Station Allocation Board")

selected_shift = st.selectbox(
    "Select Shift",
    ["Morning", "Evening", "Night"]
)


# -------------------------------------------------
# RESET BOARD WHEN SHIFT CHANGES
# -------------------------------------------------

if (
    st.session_state["previous_shift"] is not None
    and st.session_state["previous_shift"] != selected_shift
):

    st.session_state["proposed_moves"] = []
    st.session_state["pending_shift"] = None
    st.session_state["board_state"] = None
    st.session_state["board_version"] += 1

st.session_state["previous_shift"] = selected_shift


# -------------------------------------------------
# FILTER CURRENT SHIFT ALLOCATIONS
# -------------------------------------------------

shift_allocations = allocations[
    (allocations["shift"].astype(str) == selected_shift)
    & (allocations["status"].astype(str) == "Allocated")
].copy()


# -------------------------------------------------
# ORIGINAL EMPLOYEE ALLOCATION MAPPING
# -------------------------------------------------

original_allocations = dict(
    zip(
        shift_allocations["employee_id"].astype(str),
        shift_allocations["station_id"].astype(str)
    )
)


# -------------------------------------------------
# BUILD INITIAL STATION BOARD
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

            employee_card = (
                f"{employee['employee_id']} — "
                f"{employee['employee_name']} "
                f"(Score: {employee['skill_score']})"
            )

            employee_cards.append(employee_card)

        containers.append({

            "header": (
                f"{station_id} - {station_name} "
                f"({len(employee_cards)}/{capacity})"
            ),

            "items": employee_cards

        })

    return containers


# -------------------------------------------------
# INITIALIZE PERSISTENT BOARD
# -------------------------------------------------

if (
    st.session_state["board_state"] is None
    or st.session_state["board_state_shift"] != selected_shift
    or st.session_state["board_state_version"]
    != st.session_state["board_version"]
):

    st.session_state["board_state"] = build_station_board()

    st.session_state["board_state_shift"] = selected_shift

    st.session_state["board_state_version"] = (
        st.session_state["board_version"]
    )


# -------------------------------------------------
# DISPLAY DRAG AND DROP BOARD
# -------------------------------------------------

st.caption(
    "Drag employee cards between stations to preview "
    "allocation changes."
)

sorted_containers = sort_items(
    st.session_state["board_state"],
    multi_containers=True,
    key=(
        f"station_board_{selected_shift}_"
        f"{st.session_state['board_version']}"
    )
)


# -------------------------------------------------
# PRESERVE DRAGGED BOARD
# -------------------------------------------------

if isinstance(sorted_containers, list):

    st.session_state["board_state"] = sorted_containers


board = st.session_state["board_state"]


# -------------------------------------------------
# DETECT PROPOSED ALLOCATION CHANGES
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

            st.error(
                f"Unable to identify station: {header}"
            )

            break

        for employee_card in container.get("items", []):

            employee_id = (
                str(employee_card)
                .split(" — ", 1)[0]
                .strip()
            )

            if employee_id not in original_allocations:

                valid_board = False

                st.error(
                    f"Unknown employee ID: {employee_id}"
                )

                break

            if employee_id in seen_employees:

                valid_board = False

                st.error(
                    f"Duplicate employee detected: {employee_id}"
                )

                break

            seen_employees.add(employee_id)

            original_station_id = (
                original_allocations[employee_id]
            )

            if original_station_id != target_station_id:

                detected_moves.append({

                    "employee_id": employee_id,

                    "employee_name": str(employee_card),

                    "old_station": original_station_id,

                    "new_station": target_station_id

                })

        if not valid_board:
            break


# -------------------------------------------------
# VERIFY ALL EMPLOYEES ARE PRESENT
# -------------------------------------------------

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


# -------------------------------------------------
# PRESERVE PROPOSED MOVEMENTS
# -------------------------------------------------

if not valid_board:

    st.error(
        "Board validation failed. "
        "Pending movements are preserved."
    )

elif detected_moves:

    st.session_state["proposed_moves"] = (
        detected_moves.copy()
    )

    st.session_state["pending_shift"] = selected_shift


proposed_moves = st.session_state["proposed_moves"]


# -------------------------------------------------
# DEVELOPER DEBUG INFORMATION
# -------------------------------------------------

with st.expander("Developer Debug Information"):

    st.write("Original allocations:")
    st.write(original_allocations)

    st.write("Component return value:")
    st.write(sorted_containers)

    st.write("Persistent board:")
    st.write(board)

    st.write("Detected movements:")
    st.write(detected_moves)

    st.write("Saved pending movements:")
    st.write(proposed_moves)

    st.write("Pending shift:")
    st.write(st.session_state["pending_shift"])


# -------------------------------------------------
# DISPLAY PROPOSED MOVEMENTS
# -------------------------------------------------

st.divider()

st.subheader("🔄 Proposed Allocation Changes")

if proposed_moves:

    st.warning(
        f"{len(proposed_moves)} proposed movement(s) "
        "pending approval."
    )

    st.dataframe(
        pd.DataFrame(proposed_moves),
        width="stretch",
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
            "Only one movement can be approved at a time."
        )

    with st.form("manager_approval_form"):

        manager_id = st.text_input(
            "Enter Manager ID",
            value="Manager01"
        )

        confirm_changes = st.checkbox(
            "I have reviewed and approve these allocation changes."
        )

        submitted = st.form_submit_button(
            "Confirm and Save Allocation Changes",
            type="primary",
            disabled=(len(proposed_moves) != 1)
        )

    st.warning(
        "Confirmed changes will update PostgreSQL allocations "
        "and allocation audit history."
    )

    # -------------------------------------------------
    # SAVE APPROVED MOVEMENT TO POSTGRESQL
    # -------------------------------------------------

    if submitted:

        if not manager_id.strip():

            st.error("Manager ID cannot be empty.")

        elif not confirm_changes:

            st.error("Please approve the proposed movement.")

        else:

            from database_reassignment import reassign_employee_db

            move = proposed_moves[0]

            try:

                result = reassign_employee_db(
                    employee_id=move["employee_id"],
                    new_station_id=move["new_station"],
                    manager_id=manager_id.strip(),
                    allocation_date=ALLOCATION_DATE
                )

                if result:

                    st.session_state["approval_result"] = {

                        "employee_id": move["employee_id"],

                        "old_station": move["old_station"],

                        "new_station": move["new_station"],

                        "manager_id": manager_id.strip(),

                        "allocation_date": ALLOCATION_DATE

                    }

                    st.session_state["proposed_moves"] = []

                    st.session_state["pending_shift"] = None

                    load_data.clear()

                    st.success(
                        "Allocation saved successfully to PostgreSQL!"
                    )

                else:

                    st.error(
                        "Backend validation rejected the allocation. "
                        "Pending movement has been preserved."
                    )

            except Exception as error:

                st.error(
                    f"Unable to save allocation: {error}"
                )


# -------------------------------------------------
# DISCARD PROPOSED MOVEMENTS
# -------------------------------------------------

if st.button("Discard Proposed Changes"):

    st.session_state["proposed_moves"] = []

    st.session_state["pending_shift"] = None

    st.session_state["board_state"] = None

    st.session_state["board_version"] += 1

    st.rerun()


else:

    st.info(
        "Move an employee to another station "
        "to create a proposed allocation."
    )


# -------------------------------------------------
# PERSISTENT SUCCESSFUL APPROVAL RESULT
# -------------------------------------------------

if st.session_state["approval_result"]:

    approval = st.session_state["approval_result"]

    st.divider()

    st.subheader("✅ Last Successful Manager Approval")

    st.success(
        "The allocation has been successfully saved to PostgreSQL."
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Employee:** {approval['employee_id']}"
        )

        st.write(
            f"**Previous Station:** {approval['old_station']}"
        )

        st.write(
            f"**New Station:** {approval['new_station']}"
        )

    with col2:

        st.write(
            f"**Approved By:** {approval['manager_id']}"
        )

        st.write(
            f"**Allocation Date:** {approval['allocation_date']}"
        )

    st.info(
        "Your allocation is saved in PostgreSQL. "
        "The current dashboard view is intentionally not refreshed. "
        "Manually refresh the browser to load the latest data."
    )

    if st.button("Dismiss Approval Confirmation"):

        st.session_state["approval_result"] = None

        st.rerun()


# -------------------------------------------------
# MANAGER ALLOCATION AUDIT HISTORY
# -------------------------------------------------

st.divider()

st.subheader("📋 Manager Allocation Audit History")

if not audit.empty:

    st.dataframe(
        audit.sort_values(
            "id",
            ascending=False
        ),
        width="stretch",
        hide_index=True
    )

else:

    st.info("No manager allocation history available.")


# -------------------------------------------------
# END OF DASHBOARD
# -------------------------------------------------
