from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from app.models.enums import WorkPreference


class StudentTranscript(SQLModel, table=True):
    """A saved voice transcript and its optional AI-extracted profile draft."""

    __tablename__ = "student_transcripts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    student_user_id: UUID = Field(foreign_key="users.id", index=True)
    transcript: str
    extracted_name: str | None = None
    extracted_university: str | None = None
    extracted_skills: list[str] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    extracted_technical_skills: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    extracted_availability: str | None = None
    extracted_work_preference: WorkPreference | None = None
    parsing_status: str = Field(default="TRANSCRIBED_ONLY", max_length=30)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
