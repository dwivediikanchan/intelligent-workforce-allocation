
import pandas as pd

from database_repository import get_allocation_audit


def view_allocation_history(
    employee_id=None,
    manager_id=None,
    allocation_date=None
):
    print("\n========== LOADING POSTGRESQL ALLOCATION HISTORY ==========")

    history = get_allocation_audit()

    if history.empty:
        print("No allocation history available in PostgreSQL.")
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
        print("ERROR: Missing audit columns:", missing_columns)
        return

    # Filter by employee
    if employee_id:
        history = history[
            history["employee_id"].astype(str) == str(employee_id)
        ]

    # Filter by manager
    if manager_id:
        history = history[
            history["manager_id"].astype(str) == str(manager_id)
        ]

    # Filter by allocation date
    if allocation_date:
        history_dates = pd.to_datetime(
            history["allocation_date"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d")

        history = history[
            history_dates == str(allocation_date)
        ]

    if history.empty:
        print("No matching allocation history found.")
        return

    # Sort newest changes first
    history["timestamp"] = pd.to_datetime(
        history["timestamp"],
        errors="coerce"
    )

    history = history.sort_values(
        by="timestamp",
        ascending=False
    )

    print("\n========== MANAGER ALLOCATION HISTORY ==========")

    print(
        history[required_columns].to_string(index=False)
    )

    print("\nTotal history records:", len(history))
    print("Master data was read from PostgreSQL.")
    print("No PostgreSQL records were modified.")


if __name__ == "__main__":
    view_allocation_history()
