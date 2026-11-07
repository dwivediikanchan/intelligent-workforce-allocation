
import pandas as pd

from database_repository import get_defect_records


# Load original defect records from PostgreSQL
defects = get_defect_records()

# Load generated reports
station_report = pd.read_csv(
    "data/station_defect_report.csv"
)

type_report = pd.read_csv(
    "data/defect_type_report.csv"
)

breakdown = pd.read_csv(
    "data/station_defect_breakdown.csv",
    index_col="station_id"
)

if defects.empty:
    print("No defect records found in PostgreSQL.")
    raise SystemExit

print("\n========== DEFECT REPORT VALIDATION ==========")

# 1. Original total defects
original_total = defects["defect_count"].sum()

# 2. Station report total
station_total = station_report["total_defects"].sum()

# 3. Defect type report total
type_total = type_report["total_defects"].sum()

# 4. Station breakdown total
breakdown_total = breakdown.sum().sum()

print("\n--- Total Defect Comparison ---")

print("PostgreSQL Dataset:", original_total)
print("Station Report:", station_total)
print("Defect Type Report:", type_total)
print("Station Breakdown:", breakdown_total)

if len({
    original_total,
    station_total,
    type_total,
    breakdown_total
}) == 1:
    print("PASS: All defect totals match.")
else:
    print("FAIL: Defect totals do not match.")

# 5. Station coverage
print("\n--- Station Coverage ---")

if set(defects["station_id"]) == set(
    station_report["station_id"]
):
    print("PASS: All stations are included.")
else:
    print("FAIL: Station mismatch.")

# 6. Defect rate validation
print("\n--- Defect Rate Validation ---")

expected_rates = (
    station_report["total_defects"] /
    station_report["total_units_inspected"]
) * 100

if (
    expected_rates.round(2).tolist()
    == station_report["defect_rate"].round(2).tolist()
):
    print("PASS: Defect rates are consistent.")
else:
    print("FAIL: Defect rate mismatch.")

print("\n========== VALIDATION COMPLETED ==========")
