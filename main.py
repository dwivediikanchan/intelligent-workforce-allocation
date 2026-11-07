
from defect_analytics import (
    load_defect_data,
    get_station_defect_analysis,
    get_defect_type_analysis
)

from daily_allocation_engine import run_daily_allocation

from daily_allocation_summary import generate_daily_summary

from manager_dashboard_export import generate_manager_dashboard


def main():

    print("\n====================================")
    print("SMART WORKFORCE ALLOCATION SYSTEM")
    print("====================================")

    print("\n1. Run Daily Employee Allocation")
    print("2. View Station Quality Report")
    print("3. View Defect Type Report")
    print("4. View Daily Allocation Summary")
    print("5. Exit")
    print("6. Export Manager Dashboard Report")

    choice = input("\nSelect an option (1-6): ")

    if choice == "1":

        print("\nStarting Daily Allocation...")
        run_daily_allocation()

    elif choice == "2":

        defects = load_defect_data()

        report = get_station_defect_analysis(defects)

        print("\n========== STATION QUALITY REPORT ==========")
        print(report.to_string(index=False))

    elif choice == "3":

        defects = load_defect_data()

        report = get_defect_type_analysis(defects)

        print("\n========== DEFECT TYPE REPORT ==========")
        print(report.to_string(index=False))

    elif choice == "4":

        generate_daily_summary()

    elif choice == "5":

        print("\nExiting application. Goodbye!")

    elif choice == "6":

        print("\nGenerating Manager Dashboard Export...")

        generate_manager_dashboard()

    else:

        print("\nInvalid option. Please select 1, 2, 3, 4, 5, or 6.")


if __name__ == "__main__":

    main()
