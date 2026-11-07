
import pandas as pd

from database_connection import SessionLocal
from database_models import Allocation, AllocationAudit


DATA_DIR = "data"
ALLOCATION_DATE = pd.Timestamp("2026-11-04").date()


def migrate_allocations():
    db = SessionLocal()

    try:
        # Read source CSV files without modifying them
        daily_df = pd.read_csv(
            f"{DATA_DIR}/daily_allocations.csv"
        )

        audit_df = pd.read_csv(
            f"{DATA_DIR}/allocation_audit.csv"
        )

        # Validate required columns
        required_daily = {
            "employee_id", "station_id", "shift",
            "skill_score", "status"
        }

        required_audit = {
            "timestamp", "manager_id", "employee_id",
            "shift", "old_station_id", "new_station_id",
            "skill_score", "action", "allocation_date"
        }

        if not required_daily.issubset(daily_df.columns):
            raise ValueError("Daily allocation CSV has missing columns.")

        if not required_audit.issubset(audit_df.columns):
            raise ValueError("Audit CSV has missing columns.")

        # -----------------------------
        # 1. Migrate current allocations
        # -----------------------------

        valid_allocations = daily_df[
            daily_df["status"].astype(str).str.strip().str.lower()
            == "allocated"
        ].copy()

        for _, row in valid_allocations.iterrows():

            employee_id = str(row["employee_id"]).strip()
            station_id = str(row["station_id"]).strip()
            shift = str(row["shift"]).strip()

            existing = db.query(Allocation).filter_by(
                employee_id=employee_id,
                allocation_date=ALLOCATION_DATE,
                shift=shift
            ).first()

            if existing:
                # Update the existing allocation
                existing.station_id = station_id
                existing.skill_score = float(row["skill_score"])
                existing.status = "Allocated"

            else:
                db.add(Allocation(
                    employee_id=employee_id,
                    station_id=station_id,
                    allocation_date=ALLOCATION_DATE,
                    shift=shift,
                    skill_score=float(row["skill_score"]),
                    status="Allocated"
                ))

        # -----------------------------
        # 2. Migrate audit history
        # -----------------------------

        existing_audit_count = db.query(AllocationAudit).count()

        if existing_audit_count > 0:
            raise ValueError(
                "Allocation audit table is not empty. "
                "Migration stopped to prevent duplicate history."
            )

        for _, row in audit_df.iterrows():

            timestamp = pd.to_datetime(
                row["timestamp"],
                errors="raise"
            ).to_pydatetime()

            allocation_date = None

            if pd.notna(row["allocation_date"]):
                allocation_date = pd.to_datetime(
                    row["allocation_date"],
                    errors="raise"
                ).date()

            old_station = (
                str(row["old_station_id"]).strip()
                if pd.notna(row["old_station_id"])
                else None
            )

            new_station = (
                str(row["new_station_id"]).strip()
                if pd.notna(row["new_station_id"])
                else None
            )

            skill_score = (
                float(row["skill_score"])
                if pd.notna(row["skill_score"])
                else None
            )

            db.add(AllocationAudit(
                timestamp=timestamp,
                manager_id=str(row["manager_id"]).strip(),
                employee_id=str(row["employee_id"]).strip(),
                shift=str(row["shift"]).strip(),
                old_station_id=old_station,
                new_station_id=new_station,
                skill_score=skill_score,
                action=str(row["action"]).strip(),
                allocation_date=allocation_date
            ))

        # Commit allocations and audit history together
        db.commit()

        print("Allocation migration completed successfully!")
        print("Current allocations migrated:", len(valid_allocations))
        print("Audit records migrated:", len(audit_df))
        print("Allocation date:", ALLOCATION_DATE)

    except Exception as error:
        db.rollback()
        print("Migration failed. Transaction rolled back.")
        print(error)

    finally:
        db.close()


if __name__ == "__main__":
    migrate_allocations()
