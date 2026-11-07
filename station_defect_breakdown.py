
import pandas as pd

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
        .replace({"TestingFailure": "Testing Failure"})
    )

    # Create station-wise defect breakdown
    breakdown = pd.pivot_table(
        defects,
        index="station_id",
        columns="defect_type",
        values="defect_count",
        aggfunc="sum",
        fill_value=0
    )

    print("\n========== STATION DEFECT BREAKDOWN ==========")

    print(breakdown.to_string())

    # Save report
    breakdown.to_csv(
        "data/station_defect_breakdown.csv"
    )

    print("\nStation defect breakdown saved successfully!")
