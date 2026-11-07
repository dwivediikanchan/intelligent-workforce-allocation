import pandas as pd

from database_connection import SessionLocal
from database_models import SkillVerificationRecommendation
from sqlalchemy import select


CSV_FILE = "data/skill_verification_recommendations.csv"


def migrate_skill_recommendations():

    recommendations = pd.read_csv(CSV_FILE)

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        with db.begin():

            for _, row in recommendations.iterrows():

                employee_id = row["employee_id"]
                station_id = row["recommended_station"]

                existing = db.execute(
                    select(SkillVerificationRecommendation).where(
                        SkillVerificationRecommendation.employee_id
                        == employee_id,
                        SkillVerificationRecommendation.recommended_station
                        == station_id
                    )
                ).scalar_one_or_none()

                if existing:
                    skipped += 1
                    continue

                skills = [
                    skill.strip()
                    for skill in str(row["skills_to_verify"]).split(",")
                    if skill.strip()
                ]

                record = SkillVerificationRecommendation(
                    employee_id=employee_id,
                    recommended_station=station_id,
                    skills_to_verify=skills,
                    recommendation_status=row[
                        "recommendation_status"
                    ]
                )

                db.add(record)
                inserted += 1

        print("\n========== MIGRATION SUMMARY ==========")
        print("Records inserted:", inserted)
        print("Records skipped:", skipped)
        print("Migration completed successfully.")

    except Exception as error:
        print("Migration failed:", error)

    finally:
        db.close()


if __name__ == "__main__":
    migrate_skill_recommendations()