from collections.abc import Generator

from sqlalchemy import MetaData, inspect, text
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
    _make_project_title_nullable()


def _add_missing_sqlite_columns() -> None:
    """Apply the two small SQLite schema additions needed by this MVP."""
    required_columns = {
        "student_transcripts": {"extracted_technical_skills": "JSON"},
        "student_profiles": {
            "name": "TEXT",
            "technical_skills": "JSON",
        },
        "projects": {"required_technical_skills": "JSON"},
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


def _make_project_title_nullable() -> None:
    """Rebuild only legacy SQLite projects tables whose title column is NOT NULL."""
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return

    title_column = next(
        (column for column in inspector.get_columns("projects") if column["name"] == "title"),
        None,
    )
    if title_column is None or title_column["nullable"]:
        return

    # SQLite cannot drop a NOT NULL constraint. Create a replacement table, copy
    # all existing columns, then swap it in. Child tables still refer to `projects`.
    original_table = SQLModel.metadata.tables["projects"]
    replacement_metadata = MetaData()
    # Include the referenced table in this temporary metadata so SQLAlchemy can
    # compile the replacement table's owner_id foreign key.
    SQLModel.metadata.tables["users"].to_metadata(replacement_metadata)
    replacement_table = original_table.to_metadata(
        replacement_metadata,
        name="projects__title_nullable_replacement",
    )
    for index in replacement_table.indexes:
        if index.name:
            index.name = f"{index.name}_replacement"

    old_column_names = {
        column["name"] for column in inspector.get_columns("projects")
    }
    copied_column_names = [
        column.name for column in replacement_table.columns if column.name in old_column_names
    ]
    quoted_columns = ", ".join(f'"{column_name}"' for column_name in copied_column_names)

    with engine.begin() as connection:
        replacement_table.create(connection)
        connection.execute(
            text(
                "INSERT INTO projects__title_nullable_replacement "
                f"({quoted_columns}) SELECT {quoted_columns} FROM projects"
            )
        )
        connection.execute(text("DROP TABLE projects"))
        connection.execute(
            text("ALTER TABLE projects__title_nullable_replacement RENAME TO projects")
        )


def get_session() -> Generator[Session, None, None]:
    """Provide one database session for each API request."""
    with Session(engine) as session:
        yield session
