
from database_repository import get_defect_records
import pandas as pd

# Load defect data from PostgreSQL
defects = get_defect_records()

if defects.empty:
    print("No defect records found in PostgreSQL.")
    raise SystemExit

# Group data by station
station_analysis = defects.groupby("station_id").agg(
    total_defects=("defect_count", "sum"),
    total_units_inspected=("units_inspected", "sum"),
    defect_records=("defect_id", "count")
).reset_index()

# Calculate defect rate
station_analysis["defect_rate"] = (
    station_analysis["total_defects"] /
    station_analysis["total_units_inspected"]
) * 100

# Round values
station_analysis["defect_rate"] = (
    station_analysis["defect_rate"].round(2)
)

print("\n========== STATION DEFECT ANALYSIS ==========")

print(station_analysis.to_string(index=False))

# Identify station with highest defect rate
worst_station = station_analysis.loc[
    station_analysis["defect_rate"].idxmax()
]

print("\n========== QUALITY ALERT ==========")

print(
    f"Highest defect rate: {worst_station['station_id']} "
    f"({worst_station['defect_rate']}%)"
)

# Save report
station_analysis.to_csv(
    "data/station_defect_report.csv",
    index=False
)

print("\nDefect analysis report saved successfully!")
