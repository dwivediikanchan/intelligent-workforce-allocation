
import pandas as pd

allocations = pd.read_csv("data/automatic_allocations.csv")
stations = pd.read_csv("data/stations.csv")

print("\n========== STATION CAPACITY VALIDATION ==========")

active_allocations = allocations[
    allocations["status"] == "Allocated"
]

for _, station in stations.iterrows():

    station_id = station["station_id"]
    station_name = station["station_name"]
    capacity = station["capacity"]

    shifts = allocations["shift"].unique()

    for shift in shifts:

        assigned = active_allocations[
            (active_allocations["station_id"] == station_id) &
            (active_allocations["shift"] == shift)
        ].shape[0]

        print(
            f"{station_name} | {shift} | "
            f"Capacity: {capacity} | Assigned: {assigned}"
        )

        if assigned > capacity:
            print("FAIL: Station capacity exceeded.")
        else:
            print("PASS: Capacity is within limit.")


print("\n========== CAPACITY VALIDATION COMPLETED ==========")
