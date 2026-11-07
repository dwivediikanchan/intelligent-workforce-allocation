
from datetime import datetime

from sqlalchemy import select, func

from database_connection import SessionLocal
from database_models import (
    Employee,
    EmployeeSkill,
    SkillVerificationRecommendation
)


def execute_skill_verification():

    print("\n========== EXECUTE SKILL VERIFICATION ==========")

    db = SessionLocal()

    try:

        # -----------------------------------------
        # STEP 1: FETCH APPROVED RECOMMENDATIONS
        # -----------------------------------------

        print("DEBUG: Fetching approved requests...")

        approved = db.execute(
            select(SkillVerificationRecommendation)
            .where(
                SkillVerificationRecommendation.recommendation_status
                == "Approved - Verification Required"
            )
            .order_by(SkillVerificationRecommendation.id)
        ).scalars().all()

        if not approved:
            print("\nNo approved skill verification requests.")
            return

        print("\nApproved Requests:\n")

        for recommendation in approved:
            print(
                f"ID: {recommendation.id} | "
                f"Employee: {recommendation.employee_id} | "
                f"Station: {recommendation.recommended_station} | "
                f"Skills: {', '.join(recommendation.skills_to_verify)} | "
                f"Manager: {recommendation.manager_id}"
            )

        # Close read transaction before requesting input.
        db.commit()

        # -----------------------------------------
        # STEP 2: GET RECOMMENDATION ID
        # -----------------------------------------

        recommendation_id = input(
            "\nEnter Recommendation ID: "
        ).strip()

        if not recommendation_id.isdigit():
            print("\nInvalid recommendation ID.")
            return

        recommendation_id = int(recommendation_id)

        # -----------------------------------------
        # STEP 3: EXECUTE VERIFICATION
        # -----------------------------------------

        with db.begin():

            recommendation = db.execute(
                select(SkillVerificationRecommendation)
                .where(
                    SkillVerificationRecommendation.id
                    == recommendation_id
                )
                .with_for_update()
            ).scalar_one_or_none()

            if recommendation is None:
                raise ValueError("Recommendation not found.")

            if recommendation.recommendation_status != (
                "Approved - Verification Required"
            ):
                raise ValueError(
                    "Recommendation is not approved for verification."
                )

            employee_id = recommendation.employee_id
            skills = list(recommendation.skills_to_verify)

            if not skills:
                raise ValueError(
                    "No skills found in the recommendation."
                )

            # -----------------------------------------
            # STEP 4: VALIDATE EMPLOYEE
            # -----------------------------------------

            employee = db.execute(
                select(Employee).where(
                    Employee.employee_id == employee_id
                )
            ).scalar_one_or_none()

            if employee is None:
                raise ValueError("Employee does not exist.")

            # -----------------------------------------
            # STEP 5: VALIDATE ALL SKILL RECORDS
            # -----------------------------------------

            skill_records = []

            for skill_name in skills:

                record = db.execute(
                    select(EmployeeSkill)
                    .where(
                        EmployeeSkill.employee_id == employee_id,
                        func.lower(EmployeeSkill.skill_name)
                        == skill_name.lower()
                    )
                    .with_for_update()
                ).scalar_one_or_none()

                if record is None:
                    raise ValueError(
                        f"Skill record not found: {skill_name}"
                    )

                skill_records.append(record)

            # -----------------------------------------
            # STEP 6: UPDATE ALL SKILLS
            # -----------------------------------------

            for record in skill_records:
                record.verification_status = "Verified"

            # -----------------------------------------
            # STEP 7: UPDATE RECOMMENDATION STATUS
            # -----------------------------------------

            recommendation.recommendation_status = (
                "Verification Completed"
            )

            recommendation.completed_at = datetime.now()

            db.flush()

        # -----------------------------------------
        # STEP 8: DISPLAY SUCCESS
        # -----------------------------------------

        print("\nSkill verification completed successfully!")

        print("Recommendation ID:", recommendation_id)
        print("Employee:", employee_id)
        print("Station:", recommendation.recommended_station)

        print("\nVerified Skills:")

        for skill_name in skills:
            print(f"- {skill_name}")

        print("\nEmployee skills saved to PostgreSQL.")
        print("Recommendation status updated in PostgreSQL.")

        print("\n========== PROCESS FINISHED ==========")

    except Exception as error:

        db.rollback()

        print("\nVerification failed:", error)

    finally:

        db.close()


if __name__ == "__main__":
    execute_skill_verification()
