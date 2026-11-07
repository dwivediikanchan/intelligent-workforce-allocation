
import pandas as pd

from station_recommendation import generate_station_recommendations


OUTPUT_FILE = "data/station_recommendations.csv"


def save_station_recommendations(recommendation_date=None):

    # Generate latest station recommendations
    result, eligible_results = generate_station_recommendations(
        recommendation_date
    )

    # Keep only operationally recommended stations
    recommendations = eligible_results[
        eligible_results["operational_status"] == "Recommended"
    ].copy()

    if recommendations.empty:
        print("\nNo operational recommendations available.")
        return

    # Sort by employee and highest skill score
    recommendations = recommendations.sort_values(
        ["employee_id", "skill_score"],
        ascending=[True, False]
    ).copy()

    # Recalculate ranking for operational recommendations
    recommendations["recommendation_rank"] = (
        recommendations.groupby("employee_id").cumcount() + 1
    )

    # Add recommendation date
    if recommendation_date is None:
        recommendation_date = pd.Timestamp.today().strftime("%Y-%m-%d")

    recommendations.insert(
        0,
        "recommendation_date",
        recommendation_date
    )

    # Select report columns
    report_columns = [
        "recommendation_date",
        "employee_id",
        "employee_name",
        "station_id",
        "shift",
        "eligibility",
        "eligibility_reason",
        "availability_status",
        "availability_reason",
        "capacity_status",
        "capacity_reason",
        "allocated_employees",
        "station_capacity",
        "remaining_capacity",
        "operational_status",
        "skill_score",
        "is_all_rounder",
        "recommendation_rank"
    ]

    recommendations = recommendations[report_columns]

    # Save recommendations
    recommendations.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # Display saved recommendations
    print("\n========== SAVED STATION RECOMMENDATIONS ==========")

    print(
        recommendations.to_string(index=False)
    )

    print(f"\nRecommendations saved to: {OUTPUT_FILE}")

    return recommendations


if __name__ == "__main__":

    save_station_recommendations("2026-11-04")
