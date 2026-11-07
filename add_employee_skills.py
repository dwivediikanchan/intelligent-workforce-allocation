
import pandas as pd

from sqlalchemy import select, func

from database_connection import SessionLocal
from database_models import Employee, EmployeeSkill


def add_employee_skill(employee_id, skill_name, proficiency):

    # ------------------------------------------
    # 1. VALIDATE EMPLOYEE ID
    # ------------------------------------------

    if not isinstance(employee_id, str) or not employee_id.strip():
        raise ValueError("Employee ID cannot be empty.")

    employee_id = employee_id.strip()

    # ------------------------------------------
    # 2. VALIDATE SKILL NAME
    # ------------------------------------------

    if not isinstance(skill_name, str) or not skill_name.strip():
        raise ValueError("Skill name cannot be empty.")

    skill_name = skill_name.strip()

    # ------------------------------------------
    # 3. VALIDATE PROFICIENCY
    # ------------------------------------------

    if isinstance(proficiency, bool):
        raise ValueError("Proficiency must be between 1 and 5.")

    try:
        proficiency = int(proficiency)
    except (ValueError, TypeError):
        raise ValueError("Proficiency must be between 1 and 5.")

    if not 1 <= proficiency <= 5:
        raise ValueError("Proficiency must be between 1 and 5.")

    db = SessionLocal()

    try:

        with db.begin():

            # ------------------------------------------
            # 4. CHECK EMPLOYEE EXISTS
            # ------------------------------------------

            employee = db.execute(
                select(Employee).where(
                    Employee.employee_id == employee_id
                )
            ).scalar_one_or_none()

            if employee is None:
                raise ValueError("Employee does not exist.")

            # ------------------------------------------
            # 5. CHECK DUPLICATE SKILL
            # ------------------------------------------

            existing_skill = db.execute(
                select(EmployeeSkill).where(
                    EmployeeSkill.employee_id == employee_id,
                    func.lower(EmployeeSkill.skill_name)
                    == skill_name.lower()
                )
            ).scalar_one_or_none()

            if existing_skill is not None:

                raise ValueError(
                    "Employee already has this skill. "
                    "Use update_employee_skill() instead."
                )

            # ------------------------------------------
            # 6. CREATE NEW SKILL
            # ------------------------------------------

            new_skill = EmployeeSkill(
                employee_id=employee_id,
                skill_name=skill_name,
                proficiency_level=proficiency,
                verification_status="Pending"
            )

            db.add(new_skill)

            db.flush()

        # ------------------------------------------
        # 7. DISPLAY SUCCESS
        # ------------------------------------------

        result = pd.DataFrame([{
            "employee_id": employee_id,
            "skill_name": skill_name,
            "proficiency_level": proficiency,
            "verification_status": "Pending"
        }])

        print("\nSkill added successfully to PostgreSQL!")

        print(result.to_string(index=False))

        print("\nVerification status: Pending")

        return result

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":

    print("Employee skill management module")
    print("Use add_employee_skill(employee_id, skill_name, proficiency).")
