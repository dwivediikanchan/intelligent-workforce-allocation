
import pandas as pd

# Load datasets
stations = pd.read_csv("data/stations.csv")
assignments = pd.read_csv("data/current_assignments.csv")

print("\n========== STATION CAPACITY VALIDATION ==========")

# Count employees assigned to each station
station_counts = (
    assignments.groupby("station_id")
    .size()
    .reset_index(name="assigned_employees")
)

# Compare assignments with station capacity
capacity_report = stations.merge(
    station_counts,
    on="station_id",
    how="left"
)

capacity_report["assigned_employees"] = (
    capacity_report["assigned_employees"].fillna(0).astype(int)
)

capacity_report["available_capacity"] = (
    capacity_report["capacity"]
    - capacity_report["assigned_employees"]
)

# Identify capacity status
capacity_report["status"] = capacity_report.apply(
    lambda row: (
        "Over Capacity"
        if row["assigned_employees"] > row["capacity"]
        else "Within Capacity"
    ),
    axis=1
)

# Display report
print("\n--- CAPACITY REPORT ---")

print(
    capacity_report[
        [
            "station_id",
            "station_name",
            "capacity",
            "assigned_employees",
            "available_capacity",
            "status"
        ]
    ].to_string(index=False)
)

# Display over-capacity stations
print("\n--- CAPACITY VIOLATIONS ---")

violations = capacity_report[
    capacity_report["status"] == "Over Capacity"
]

if not violations.empty:
    print(violations.to_string(index=False))
else:
    print("No capacity violations found.")

print("\n========== VALIDATION COMPLETED ==========")
