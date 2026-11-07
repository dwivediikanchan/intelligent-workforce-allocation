
import os

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker, declarative_base


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

def get_database_url():

    # 1. Check environment variable
    database_url = os.getenv("DATABASE_URL")

    # 2. Check Streamlit Cloud secrets
    if not database_url:
        try:
            database_url = st.secrets.get("DATABASE_URL")
        except Exception:
            database_url = None

    # 3. Use hosted database URL if available
    if database_url:
        url = make_url(database_url)

        # Use psycopg driver
        url = url.set(drivername="postgresql+psycopg")

        return url

    # 4. Otherwise use local PostgreSQL environment variables
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "smart_workforce_db")

    if not DB_PASSWORD:
        raise ValueError(
            "Configure DATABASE_URL in Streamlit Secrets "
            "or DB_PASSWORD in local environment variables."
        )

    from sqlalchemy.engine import URL

    return URL.create(
        drivername="postgresql+psycopg",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME
    )


DATABASE_URL = get_database_url()


# ==========================================
# DATABASE ENGINE
# ==========================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


# ==========================================
# DATABASE SESSION
# ==========================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ==========================================
# TEST CONNECTION
# ==========================================

def test_connection():

    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT version()")
        )

        print("PostgreSQL connection successful!")

        print(result.scalar())


if __name__ == "__main__":
    test_connection()
