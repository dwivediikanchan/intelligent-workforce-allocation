
import pandas as pd

from database_repository import (
    get_defect_records,
    get_stations
)


# Load data from PostgreSQL
defects = get_defect_records()
stations = get_stations()

if defects.empty:
    print("No defect records found in PostgreSQL.")
    raise SystemExit

print("========== DEFECT DATA QUALITY CHECK ==========")

# 1. Check missing values
print("\n--- Missing Values ---")
print(defects.isnull().sum())

# 2. Check duplicate defect IDs
print("\n--- Duplicate Defect IDs ---")

if defects["defect_id"].duplicated().any():
    print("FAIL: Duplicate defect IDs found.")
else:
    print("PASS: No duplicate defect IDs.")

# 3. Validate defect counts
print("\n--- Defect Count Validation ---")

if (defects["defect_count"] < 0).any():
    print("FAIL: Negative defect counts found.")
else:
    print("PASS: Defect counts are valid.")

# 4. Validate inspected units
print("\n--- Units Inspected Validation ---")

if (defects["units_inspected"] <= 0).any():
    print("FAIL: Invalid inspected unit counts.")
else:
    print("PASS: Inspected unit counts are valid.")

# 5. Validate station IDs
print("\n--- Station Validation ---")

valid_stations = set(stations["station_id"])

invalid_stations = set(
    defects["station_id"]
) - valid_stations

if invalid_stations:
    print("FAIL: Invalid stations:", invalid_stations)
else:
    print("PASS: All station IDs are valid.")

# 6. Validate dates
print("\n--- Date Validation ---")

defects["production_date"] = pd.to_datetime(
    defects["production_date"],
    errors="coerce"
)

if defects["production_date"].isnull().any():
    print("FAIL: Invalid production dates found.")
else:
    print("PASS: All production dates are valid.")

print("\n========== VALIDATION COMPLETED ==========")
