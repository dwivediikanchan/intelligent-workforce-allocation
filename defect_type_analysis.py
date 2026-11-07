
from database_repository import get_defect_records

# Load defect records from PostgreSQL
defects = get_defect_records()

if defects.empty:
    print("No defect records found in PostgreSQL.")

else:
    # Clean defect type labels
    defects["defect_type"] = (
        defects["defect_type"]
        .str.strip()
        .replace({
            "TestingFailure": "Testing Failure"
        })
    )

    # Aggregate by defect type
    defect_type_summary = defects.groupby(
        "defect_type"
    ).agg(
        total_defects=("defect_count", "sum"),
        affected_stations=("station_id", "nunique")
    ).reset_index()

    # Sort by defect count
    defect_type_summary = defect_type_summary.sort_values(
        by="total_defects",
        ascending=False
    )

    print("\n========== DEFECT TYPE ANALYSIS ==========")

    print(defect_type_summary.to_string(index=False))

    # Save report
    defect_type_summary.to_csv(
        "data/defect_type_report.csv",
        index=False
    )

    print("\nDefect type report saved successfully!")
