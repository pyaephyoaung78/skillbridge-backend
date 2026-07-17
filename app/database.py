from collections.abc import Generator

from sqlmodel import SQLModel, Session, create_engine

DATABASE_URL = "sqlite:///./skillbridge.db"

# SQLite needs this option because FastAPI handles requests in different threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    """Create all SQLModel tables registered by future model files."""
    # Importing models registers them with SQLModel before creating tables.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Provide one database session for each API request."""
    with Session(engine) as session:
        yield session
