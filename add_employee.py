
from sqlalchemy import select

from database_connection import SessionLocal
from database_models import Employee


def add_employee(name, experience, shift):

    # -----------------------------------------
    # 1. VALIDATE EMPLOYEE DETAILS
    # -----------------------------------------

    if not isinstance(name, str) or not name.strip():
        raise ValueError("Employee name cannot be empty.")

    if isinstance(experience, bool):
        raise ValueError("Experience must be a valid number.")

    try:
        experience = float(experience)
    except (ValueError, TypeError):
        raise ValueError("Experience must be a valid number.")

    if experience < 0 or not experience.is_integer():
        raise ValueError(
            "Experience must be a non-negative whole number."
        )

    experience = int(experience)

    valid_shifts = ["Morning", "Evening", "Night"]

    if shift not in valid_shifts:
        raise ValueError("Invalid shift.")

    db = SessionLocal()

    try:

        # -----------------------------------------
        # 2. GENERATE UNIQUE EMPLOYEE ID
        # -----------------------------------------

        with db.begin():

            existing_ids = db.execute(
                select(Employee.employee_id)
            ).scalars().all()

            existing_numbers = []

            for existing_id in existing_ids:

                if (
                    isinstance(existing_id, str)
                    and existing_id.startswith("E")
                    and existing_id[1:].isdigit()
                ):
                    existing_numbers.append(
                        int(existing_id[1:])
                    )

            next_number = (
                max(existing_numbers) + 1
                if existing_numbers
                else 101
            )

            employee_id = f"E{next_number:03d}"

            # -----------------------------------------
            # 3. CREATE EMPLOYEE RECORD
            # -----------------------------------------

            new_employee = Employee(
                employee_id=employee_id,
                employee_name=name.strip(),
                experience_years=experience,
                shift=shift,
                status="Active"
            )

            # -----------------------------------------
            # 4. SAVE TO POSTGRESQL
            # -----------------------------------------

            db.add(new_employee)
            db.flush()

        print("\nEmployee added successfully to PostgreSQL!")

        print("-----------------------------------")
        print("Employee ID:", employee_id)
        print("Employee Name:", name.strip())
        print("Experience:", experience)
        print("Shift:", shift)
        print("Status: Active")
        print("-----------------------------------")

        return employee_id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":

    print("Employee registration module")
    print("Use add_employee(name, experience, shift) to register an employee.")
