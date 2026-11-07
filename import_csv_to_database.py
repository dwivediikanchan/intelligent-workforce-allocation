
import pandas as pd

from database_connection import SessionLocal
from database_models import DefectRecord


DATA_DIR = "data"


def import_defect_data():
    db = SessionLocal()

    try:
        defects_df = pd.read_csv(
            f"{DATA_DIR}/defect_records.csv"
        )

        required_columns = [
            "defect_id",
            "production_date",
            "station_id",
            "defect_type",
            "defect_count",
            "units_inspected"
        ]

        missing = [
            column for column in required_columns
            if column not in defects_df.columns
        ]

        if missing:
            raise ValueError(
                f"Missing columns in defect CSV: {missing}"
            )

        if defects_df["defect_id"].duplicated().any():
            raise ValueError(
                "Duplicate defect IDs found in CSV."
            )

        for _, row in defects_df.iterrows():
            record = DefectRecord(
                defect_id=str(row["defect_id"]),
                production_date=pd.to_datetime(
                    row["production_date"]
                ).date(),
                station_id=str(row["station_id"]),
                defect_type=str(row["defect_type"]),
                defect_count=int(row["defect_count"]),
                units_inspected=int(row["units_inspected"])
            )

            db.merge(record)

        db.commit()

        print("Defect records imported successfully!")
        print("CSV records:", len(defects_df))

        total_records = db.query(DefectRecord).count()
        print("PostgreSQL defect records:", total_records)

    except Exception as error:
        db.rollback()
        print("Defect import failed. Changes rolled back.")
        print("Error:", error)

    finally:
        db.close()


if __name__ == "__main__":
    import_defect_data()
