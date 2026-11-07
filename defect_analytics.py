
import pandas as pd

from database_repository import get_defect_records


def load_defect_data():
    """Load manufacturing defect records from PostgreSQL."""

    defects = get_defect_records()

    if defects.empty:
        return defects

    defects["production_date"] = pd.to_datetime(
        defects["production_date"],
        errors="coerce"
    )

    defects["defect_type"] = (
        defects["defect_type"]
        .str.strip()
        .replace({
            "TestingFailure": "Testing Failure"
        })
    )

    return defects


def get_station_defect_analysis(defects):
    """Calculate station-wise defect rates."""

    report = defects.groupby("station_id").agg(
        total_defects=("defect_count", "sum"),
        total_units_inspected=("units_inspected", "sum")
    ).reset_index()

    report["defect_rate"] = (
        report["total_defects"] /
        report["total_units_inspected"]
    ) * 100

    report["defect_rate"] = report[
        "defect_rate"
    ].round(2)

    return report


def get_defect_type_analysis(defects):
    """Summarize defects by type."""

    return defects.groupby("defect_type").agg(
        total_defects=("defect_count", "sum"),
        affected_stations=("station_id", "nunique")
    ).reset_index().sort_values(
        "total_defects",
        ascending=False
    )


def get_station_defect_breakdown(defects):
    """Create station-wise defect breakdown."""

    return pd.pivot_table(
        defects,
        index="station_id",
        columns="defect_type",
        values="defect_count",
        aggfunc="sum",
        fill_value=0
    )


if __name__ == "__main__":

    defects = load_defect_data()

    if defects.empty:
        print("No defect records found in PostgreSQL.")

    else:
        station_report = get_station_defect_analysis(
            defects
        )

        type_report = get_defect_type_analysis(
            defects
        )

        breakdown = get_station_defect_breakdown(
            defects
        )

        print("\n========== CENTRAL DEFECT ANALYTICS ==========")

        print("\n--- Station Analysis ---")
        print(station_report.to_string(index=False))

        print("\n--- Defect Type Analysis ---")
        print(type_report.to_string(index=False))

        print("\n--- Station Defect Breakdown ---")
        print(breakdown.to_string())

        print("\nDefect analytics completed successfully!")
