
import pandas as pd

# Load assignment data
assignments = pd.read_csv("data/current_assignments.csv")

print("\n========== EMPLOYEE ASSIGNMENT VALIDATION ==========")

# Check 1: Duplicate assignment records
print("\n--- DUPLICATE ASSIGNMENTS ---")

duplicates = assignments[
    assignments.duplicated(
        subset=["employee_id", "station_id", "shift"],
        keep=False
    )
]

if not duplicates.empty:
    print(duplicates.to_string(index=False))
else:
    print("No duplicate assignments found.")


# Check 2: Employees assigned to multiple stations
# during the same shift
print("\n--- MULTIPLE STATION ASSIGNMENTS ---")

station_counts = (
    assignments.groupby(["employee_id", "shift"])["station_id"]
    .nunique()
    .reset_index(name="station_count")
)

conflicts = station_counts[
    station_counts["station_count"] > 1
]

if not conflicts.empty:
    print(conflicts.to_string(index=False))
else:
    print("No multiple station assignment conflicts found.")


# Check 3: Display employees working in different shifts
print("\n--- EMPLOYEE SHIFT ASSIGNMENTS ---")

shift_report = (
    assignments.groupby("employee_id")["shift"]
    .nunique()
    .reset_index(name="number_of_shifts")
)

print(shift_report.to_string(index=False))

print("\n========== VALIDATION COMPLETED ==========")
