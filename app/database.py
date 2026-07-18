from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///./skillbridge.db"

# SQLite needs this option because FastAPI handles requests in different threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    """Create all SQLModel tables registered by future model files."""
    # Importing models registers them with SQLModel before creating tables.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _add_missing_sqlite_columns()


def _add_missing_sqlite_columns() -> None:
    """Apply the two small SQLite schema additions needed by this MVP."""
    required_columns = {
        "student_transcripts": {"extracted_technical_skills": "JSON"},
        "student_profiles": {
            "name": "TEXT",
            "technical_skills": "JSON",
        },
    }
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table_name, columns in required_columns.items():
            if table_name not in existing_tables:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table_name)
            }
            for column_name, column_type in columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                    )


def get_session() -> Generator[Session, None, None]:
    """Provide one database session for each API request."""
    with Session(engine) as session:
        yield session
