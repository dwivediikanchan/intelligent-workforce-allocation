
from database_reassignment import reassign_employee_db


def reassign_employee(
    employee_id,
    new_station_id,
    manager_id,
    allocation_date="2026-11-04"
):
    """
    Reassign an employee using PostgreSQL.

    All validation, allocation updates, and audit logging
    are handled by the database transaction.
    """

    return reassign_employee_db(
        employee_id=employee_id,
        new_station_id=new_station_id,
        manager_id=manager_id,
        allocation_date=allocation_date
    )


# -------------------------------------------------
# TEST EXECUTION
# -------------------------------------------------

if __name__ == "__main__":

    result = reassign_employee(
        employee_id="E107",
        new_station_id="S01",
        manager_id="Manager01",
        allocation_date="2026-11-04"
    )

    if result:
        print("PostgreSQL reassignment completed successfully.")
    else:
        print("Reassignment rejected by backend validation.")
