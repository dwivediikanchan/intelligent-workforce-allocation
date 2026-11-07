
import pandas as pd

allocations = pd.read_csv("data/automatic_allocations.csv")

print("\n========== ASSIGNMENT CONFLICT VALIDATION ==========")

# Consider only allocated employees
active_allocations = allocations[
    allocations["status"] == "Allocated"
]

# Check whether an employee has multiple stations in one shift
conflicts = (
    active_allocations
    .groupby(["employee_id", "shift"])["station_id"]
    .nunique()
    .reset_index(name="station_count")
)

conflicts = conflicts[
    conflicts["station_count"] > 1
]

if conflicts.empty:
    print("PASS: No employee is assigned to multiple stations in the same shift.")
else:
    print("FAIL: Conflicting employee assignments found.")
    print(conflicts.to_string(index=False))


# Check duplicate employee-station-shift records
duplicates = active_allocations[
    active_allocations.duplicated(
        subset=["employee_id", "station_id", "shift"],
        keep=False
    )
]

if duplicates.empty:
    print("PASS: No duplicate assignment records.")
else:
    print("FAIL: Duplicate assignment records found.")
    print(duplicates.to_string(index=False))


print("\n========== VALIDATION COMPLETED ==========")
