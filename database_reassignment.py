
from datetime import datetime, date

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from database_connection import SessionLocal
from database_models import (
    Employee,
    EmployeeSkill,
    Station,
    StationRequirement,
    Attendance,
    Allocation,
    AllocationAudit
)


def reassign_employee_db(
    employee_id,
    new_station_id,
    manager_id,
    allocation_date="2026-11-04"
):
    """
    Reassign an employee using PostgreSQL.

    Allocation and audit history are saved in one transaction.
    If anything fails, both operations are rolled back.
    """

    db = SessionLocal()

    try:
        allocation_date = date.fromisoformat(str(allocation_date))

        with db.begin():

            # 1. Validate active employee
            employee = db.execute(
                select(Employee).where(
                    Employee.employee_id == employee_id,
                    Employee.status == "Active"
                )
            ).scalar_one_or_none()

            if employee is None:
                raise ValueError(
                    "Employee does not exist or is inactive."
                )

            employee_name = employee.employee_name
            employee_shift = employee.shift

            # 2. Validate attendance
            attendance = db.execute(
                select(Attendance).where(
                    Attendance.employee_id == employee_id,
                    Attendance.attendance_date == allocation_date,
                    Attendance.shift == employee_shift,
                    Attendance.attendance_status == "Present"
                )
            ).scalar_one_or_none()

            if attendance is None:
                raise ValueError(
                    "Employee is absent, on leave, or shift mismatched."
                )

            # 3. Validate destination station
            station = db.execute(
                select(Station).where(
                    Station.station_id == new_station_id
                )
            ).scalar_one_or_none()

            if station is None:
                raise ValueError("Invalid destination station.")

            # 4. Find current allocation for this date and shift
            current_allocations = db.execute(
                select(Allocation).where(
                    Allocation.employee_id == employee_id,
                    Allocation.allocation_date == allocation_date,
                    Allocation.shift == employee_shift,
                    Allocation.status == "Allocated"
                ).with_for_update()
            ).scalars().all()

            if len(current_allocations) > 1:
                raise ValueError(
                    "Employee has multiple active allocations."
                )

            current = (
                current_allocations[0]
                if current_allocations
                else None
            )

            old_station_id = None

            if current is not None:
                old_station_id = current.station_id

                if old_station_id == new_station_id:
                    raise ValueError(
                        "Employee is already assigned to this station."
                    )

            # 5. Load verified skills
            verified_skills = db.execute(
                select(EmployeeSkill).where(
                    EmployeeSkill.employee_id == employee_id,
                    EmployeeSkill.verification_status == "Verified"
                )
            ).scalars().all()

            skill_map = {
                skill.skill_name.strip().lower():
                skill.proficiency_level
                for skill in verified_skills
            }

            # 6. Validate station requirements
            station_rules = db.execute(
                select(StationRequirement).where(
                    StationRequirement.station_id == new_station_id
                )
            ).scalars().all()

            if not station_rules:
                raise ValueError(
                    "Station requirements are not configured."
                )

            score = 0.0

            for rule in station_rules:

                skill_name = rule.skill_name.strip().lower()
                level = skill_map.get(skill_name, 0)

                if rule.mandatory and level < rule.min_proficiency:
                    raise ValueError(
                        f"Missing mandatory verified skill: "
                        f"{rule.skill_name}"
                    )

                score += (
                    (level / 5)
                    * rule.weight
                    * 100
                )

            score = round(score, 2)

            # 7. Validate destination capacity
            occupied = db.execute(
                select(func.count(Allocation.id)).where(
                    Allocation.station_id == new_station_id,
                    Allocation.allocation_date == allocation_date,
                    Allocation.shift == employee_shift,
                    Allocation.status == "Allocated",
                    Allocation.employee_id != employee_id
                )
            ).scalar_one()

            if occupied >= station.capacity:
                raise ValueError(
                    "Destination station has reached its capacity."
                )

            # 8. Prevent conflicting allocations on another shift
            conflicting = db.execute(
                select(Allocation.id).where(
                    Allocation.employee_id == employee_id,
                    Allocation.allocation_date == allocation_date,
                    Allocation.shift != employee_shift,
                    Allocation.status == "Allocated"
                )
            ).first()

            if conflicting:
                raise ValueError(
                    "Employee has a conflicting active allocation."
                )

            # 9. Update or create allocation
            if current is not None:

                current.station_id = new_station_id
                current.skill_score = score
                current.status = "Allocated"

            else:

                current = Allocation(
                    employee_id=employee_id,
                    station_id=new_station_id,
                    allocation_date=allocation_date,
                    shift=employee_shift,
                    skill_score=score,
                    status="Allocated"
                )

                db.add(current)

            # 10. Add audit record in the same transaction
            audit = AllocationAudit(
                timestamp=datetime.now(),
                manager_id=manager_id,
                employee_id=employee_id,
                shift=employee_shift,
                old_station_id=old_station_id,
                new_station_id=new_station_id,
                skill_score=score,
                action=(
                    "Manual Reassignment"
                    if old_station_id is not None
                    else "Manual Allocation"
                ),
                allocation_date=allocation_date
            )

            db.add(audit)

        # Transaction committed successfully.
        print("\n========== POSTGRESQL ALLOCATION SUCCESSFUL ==========")
        print("Employee:", employee_id)
        print("Employee Name:", employee_name)
        print("Previous Station:", old_station_id or "Not Assigned")
        print("New Station:", new_station_id)
        print("Shift:", employee_shift)
        print("Skill Score:", score)
        print("Manager:", manager_id)
        print("Allocation Date:", allocation_date)

        return True

    except (ValueError, SQLAlchemyError) as error:

        db.rollback()

        print("\nPOSTGRESQL ALLOCATION FAILED:")
        print(error)

        return False

    finally:
        db.close()


if __name__ == "__main__":

    reassign_employee_db(
        employee_id="E107",
        new_station_id="S01",
        manager_id="Manager01",
        allocation_date="2026-11-04"
    )
