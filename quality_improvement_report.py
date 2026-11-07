
from defect_analytics import (
    load_defect_data,
    get_station_defect_analysis,
    get_defect_type_analysis
)


# Load defect records from PostgreSQL
defects = load_defect_data()

if defects.empty:
    print("No defect records found in PostgreSQL.")

else:
    # Generate reports directly from database records
    station_report = get_station_defect_analysis(defects)
    defect_report = get_defect_type_analysis(defects)

    print("\n========== QUALITY IMPROVEMENT REPORT ==========")

    # Station with highest defect rate
    worst_station = station_report.loc[
        station_report["defect_rate"].idxmax()
    ]

    print("\n--- Station Requiring Attention ---")

    print(
        f"Station: {worst_station['station_id']}\n"
        f"Defect Rate: {worst_station['defect_rate']}%"
    )

    # Highest defect type
    worst_defect = defect_report.loc[
        defect_report["total_defects"].idxmax()
    ]

    print("\n--- Most Frequent Defect ---")

    print(
        f"Defect Type: {worst_defect['defect_type']}\n"
        f"Total Defects: {worst_defect['total_defects']}"
    )

    # Cross-station defect types
    print("\n--- Defects Across Multiple Stations ---")

    cross_station = defect_report[
        defect_report["affected_stations"] > 1
    ]

    if cross_station.empty:
        print("No cross-station defect patterns found.")
    else:
        print(cross_station.to_string(index=False))

    # Save manager report
    with open(
        "data/quality_improvement_report.txt",
        "w"
    ) as file:

        file.write("QUALITY IMPROVEMENT REPORT\n\n")

        file.write(
            f"Highest Defect Rate Station: "
            f"{worst_station['station_id']}\n"
        )

        file.write(
            f"Defect Rate: {worst_station['defect_rate']}%\n\n"
        )

        file.write(
            f"Most Frequent Defect: "
            f"{worst_defect['defect_type']}\n"
        )

        file.write(
            f"Total Defects: {worst_defect['total_defects']}\n"
        )

        file.write("\nCross-Station Defects:\n")
        file.write(cross_station.to_string(index=False))

    print("\nQuality improvement report saved successfully!")
