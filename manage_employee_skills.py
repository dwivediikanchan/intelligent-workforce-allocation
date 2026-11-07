
import pandas as pd

from sqlalchemy import select, func

from database_connection import SessionLocal
from database_models import Employee, EmployeeSkill


def update_employee_skill(
    employee_id,
    skill_name,
    proficiency
):

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
            # 5. FIND EXISTING SKILL
            # ------------------------------------------

            existing_skill = db.execute(
                select(EmployeeSkill).where(
                    EmployeeSkill.employee_id == employee_id,
                    func.lower(EmployeeSkill.skill_name)
                    == skill_name.lower()
                )
            ).scalar_one_or_none()

            if existing_skill is not None:

                # ------------------------------------------
                # 6. UPDATE EXISTING SKILL
                # ------------------------------------------

                proficiency_changed = (
                    existing_skill.proficiency_level != proficiency
                )

                existing_skill.proficiency_level = proficiency

                if proficiency_changed:

                    existing_skill.verification_status = "Pending"

                    print("\nExisting employee skill updated.")
                    print("Skill requires re-verification.")

                else:

                    print("\nProficiency is unchanged.")
                    print("Existing verification status preserved.")

            else:

                # ------------------------------------------
                # 7. INSERT NEW SKILL
                # ------------------------------------------

                new_skill = EmployeeSkill(
                    employee_id=employee_id,
                    skill_name=skill_name,
                    proficiency_level=proficiency,
                    verification_status="Pending"
                )

                db.add(new_skill)

                print("\nNew employee skill added.")
                print("Verification status: Pending")

            db.flush()

        # ------------------------------------------
        # 8. FETCH COMPLETE EMPLOYEE SKILL REPORT
        # ------------------------------------------

        db.expire_all()

        employee_skills = db.execute(
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
            for record in employee_skills
        ])

        print("\nEmployee skill management completed.")

        print(report.to_string(index=False))

        return report

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":

    print("PostgreSQL employee skill management module")
    print(
        "Use update_employee_skill("
        "employee_id, skill_name, proficiency)."
    )
