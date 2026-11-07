
from datetime import datetime
from sqlalchemy import select

from database_connection import SessionLocal
from database_models import SkillVerificationRecommendation


def approve_skill_recommendation():

    print("\n========== MANAGER SKILL VERIFICATION APPROVAL ==========")

    db = SessionLocal()

    try:
        print("DEBUG: Before database query")

        pending = db.execute(
            select(SkillVerificationRecommendation)
            .where(
                SkillVerificationRecommendation.recommendation_status
                == "Pending Manager Approval"
            )
            .order_by(SkillVerificationRecommendation.id)
        ).scalars().all()

        print("DEBUG: Query completed")
        print("DEBUG: Pending count:", len(pending))

        if not pending:
            print("\nNo pending recommendations.")
            return

        print("\nPending Recommendations:\n")

        for recommendation in pending:
            print(
                f"ID: {recommendation.id} | "
                f"Employee: {recommendation.employee_id} | "
                f"Station: {recommendation.recommended_station} | "
                f"Skills: {', '.join(recommendation.skills_to_verify)} | "
                f"Status: {recommendation.recommendation_status}"
            )

        # Close the read transaction before requesting input.
        db.commit()

        recommendation_id = input(
            "\nEnter Recommendation ID to approve: "
        ).strip()

        if not recommendation_id.isdigit():
            print("\nInvalid recommendation ID.")
            return

        recommendation_id = int(recommendation_id)

        manager_id = input("Enter Manager ID: ").strip()

        if not manager_id:
            print("\nManager ID cannot be empty.")
            return

        # Start a fresh transaction and lock the selected record.
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
                "Pending Manager Approval"
            ):
                raise ValueError(
                    "Recommendation is not pending approval."
                )

            recommendation.recommendation_status = (
                "Approved - Verification Required"
            )
            recommendation.manager_id = manager_id
            recommendation.approved_at = datetime.now()

            employee_id = recommendation.employee_id
            station_id = recommendation.recommended_station
            skills = list(recommendation.skills_to_verify)

        print("\nRecommendation approved successfully!")
        print("Recommendation ID:", recommendation_id)
        print("Employee:", employee_id)
        print("Station:", station_id)
        print("Manager:", manager_id)
        print("Skills:", ", ".join(skills))

        print("\nNote: Skill verification itself has not been performed.")
        print("\n========== APPROVAL PROCESS COMPLETED ==========")

    except Exception as error:
        db.rollback()
        print("\nApproval failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    approve_skill_recommendation()
