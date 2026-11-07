
import pandas as pd

from sqlalchemy import select

from database_connection import SessionLocal
from database_models import (
    Employee,
    EmployeeSkill,
    Station,
    StationRequirement,
    Attendance,
    Allocation,
    AllocationAudit,
    DefectRecord
)


def fetch_table(model):
    """Fetch all records from a database model as a DataFrame."""

    db = SessionLocal()

    try:
        records = db.execute(select(model)).scalars().all()

        data = [
            {
                column.name: getattr(record, column.name)
                for column in model.__table__.columns
            }
            for record in records
        ]

        return pd.DataFrame(data)

    finally:
        db.close()


def get_employees():
    return fetch_table(Employee)


def get_employee_skills():
    return fetch_table(EmployeeSkill)


def get_stations():
    return fetch_table(Station)


def get_station_requirements():
    return fetch_table(StationRequirement)


def get_attendance():
    return fetch_table(Attendance)


def get_allocations():
    return fetch_table(Allocation)


def get_allocation_audit():
    return fetch_table(AllocationAudit)


def get_defect_records():
    return fetch_table(DefectRecord)


if __name__ == "__main__":

    print("\nEMPLOYEES")
    print(get_employees())

    print("\nEMPLOYEE SKILLS")
    print(get_employee_skills())

    print("\nSTATIONS")
    print(get_stations())

    print("\nSTATION REQUIREMENTS")
    print(get_station_requirements())

    print("\nATTENDANCE")
    print(get_attendance())

    print("\nDEFECT RECORDS")
    print(get_defect_records().to_string(index=False))
