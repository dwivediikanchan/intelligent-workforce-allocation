
from database_connection import engine, Base
import database_models


def initialize_database():
    try:
        Base.metadata.create_all(bind=engine)

        print("Database tables created successfully!")

        for table_name in Base.metadata.tables:
            print(f"Created/verified: {table_name}")

    except Exception as error:
        print("Database initialization failed:")
        print(error)


if __name__ == "__main__":
    initialize_database()
