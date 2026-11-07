
import pandas as pd

from sqlalchemy import select, func

from database_connection import SessionLocal
from database_models import Employee, EmployeeSkill


def verify_employee_skill(employee_id, skill_name):

    if not isinstance(employee_id, str) or not employee_id.strip():
        raise ValueError("Employee ID cannot be empty.")

    if not isinstance(skill_name, str) or not skill_name.strip():
        raise ValueError("Skill name cannot be empty.")

    employee_id = employee_id.strip()
    skill_name = skill_name.strip()

    db = SessionLocal()

    try:

        with db.begin():

            # Check employee exists
            employee = db.execute(
                select(Employee).where(
                    Employee.employee_id == employee_id
                )
            ).scalar_one_or_none()

            if employee is None:
                raise ValueError("Employee does not exist.")

            # Find employee skill
            skill = db.execute(
                select(EmployeeSkill).where(
                    EmployeeSkill.employee_id == employee_id,
                    func.lower(EmployeeSkill.skill_name)
                    == skill_name.lower()
                )
            ).scalar_one_or_none()

            if skill is None:
                raise ValueError("Employee skill not found.")

            if skill.verification_status == "Verified":
                print("\nSkill is already verified.")

            else:
                skill.verification_status = "Verified"
                print("\nSkill verified successfully!")

            db.flush()

        # Fetch updated skill report
        db.expire_all()

        records = db.execute(
            select(EmployeeSkill).where(
                EmployeeSkill.employee_id == employee_id
            ).order_by(EmployeeSkill.skill_name)
        ).scalars().all()

        report = pd.DataFrame([
            {
                "employee_id": record.employee_id,
                "skill_name": record.skill_name,
                "proficiency_level": record.proficiency_level,
                "verification_status": record.verification_status
            }
            for record in records
        ])

        print("\nUpdated employee skill report:")
        print(report.to_string(index=False))

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    print("PostgreSQL employee skill verification module is ready.")
