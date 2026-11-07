
import pandas as pd

from database_repository import (
    get_allocations,
    get_stations
)


def generate_manager_dashboard():

    # ==========================================
    # STEP 1: LOAD DATA FROM POSTGRESQL
    # ==========================================

    allocations = get_allocations()
    stations = get_stations()

    if stations.empty:
        raise ValueError("No station records found in PostgreSQL.")

    required_allocation_columns = {
        "employee_id",
        "station_id",
        "shift",
        "skill_score",
        "status"
    }

    missing = required_allocation_columns - set(allocations.columns)

    if missing:
        raise ValueError(
            f"Allocation data is missing columns: {sorted(missing)}"
        )

    # Add employee names if the allocation table does not contain them.
    if "employee_name" not in allocations.columns:
        from database_repository import get_employees

        employees = get_employees()

        allocations = allocations.merge(
            employees[["employee_id", "employee_name"]],
            on="employee_id",
            how="left"
        )

    # ==========================================
    # STEP 2: EMPLOYEE ALLOCATION REPORT
    # ==========================================

    employee_report = allocations[
        [
            "employee_id",
            "employee_name",
            "station_id",
            "shift",
            "skill_score",
            "status"
        ]
    ].copy()

    employee_report["report_type"] = "Employee Allocation"

    # ==========================================
    # STEP 3: STATION UTILIZATION REPORT
    # ==========================================

    station_records = []

    for _, station in stations.iterrows():

        station_id = station["station_id"]
        capacity = int(station["capacity"])

        for shift in ["Morning", "Evening"]:

            count = len(
                allocations[
                    (allocations["station_id"] == station_id)
                    & (allocations["shift"] == shift)
                    & (allocations["status"] == "Allocated")
                ]
            )

            utilization = (
                (count / capacity) * 100
                if capacity > 0 else 0
            )

            station_records.append({

                "employee_id": "",
                "employee_name": "",
                "station_id": station_id,
                "shift": shift,
                "skill_score": "",
                "status": "Station Utilization",
                "report_type": "Station Capacity",
                "allocated_employees": count,
                "capacity": capacity,
                "utilization_percentage": round(
                    utilization, 2
                )

            })

    station_report = pd.DataFrame(station_records)

    # ==========================================
    # STEP 4: PREPARE EMPLOYEE REPORT COLUMNS
    # ==========================================

    employee_report["allocated_employees"] = ""
    employee_report["capacity"] = ""
    employee_report["utilization_percentage"] = ""

    # ==========================================
    # STEP 5: COMBINE REPORTS
    # ==========================================

    report_columns = [
        "employee_id",
        "employee_name",
        "station_id",
        "shift",
        "skill_score",
        "status",
        "report_type",
        "allocated_employees",
        "capacity",
        "utilization_percentage"
    ]

    employee_report = employee_report[report_columns]
    station_report = station_report[report_columns]

    manager_report = pd.concat(
        [employee_report, station_report],
        ignore_index=True
    )

    # ==========================================
    # STEP 6: SAVE MANAGER REPORT
    # ==========================================

    manager_report.to_csv(
        "data/manager_dashboard_report.csv",
        index=False
    )

    print("\n========== MANAGER DASHBOARD EXPORT ==========")

    print(manager_report.to_string(index=False))

    print(
        "\nManager dashboard report saved successfully!"
    )

    return manager_report


if __name__ == "__main__":

    generate_manager_dashboard()
