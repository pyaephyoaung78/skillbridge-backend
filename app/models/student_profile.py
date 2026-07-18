from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.models.enums import WorkPreference


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StudentProfile(SQLModel, table=True):
    """The skills and work preferences used to match a student to projects."""

    __tablename__ = "student_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_student_profile_user_id"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(index=True, foreign_key="users.id")
    university: str = Field(min_length=1, max_length=150)
    skills: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    technical_skills: list[str] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    availability: str = Field(min_length=1, max_length=50)
    work_preference: WorkPreference
    portfolio_url: str | None = Field(default=None, max_length=500)
    rating: float = Field(default=0, ge=0, le=5)
    completed_projects: int = Field(default=0, ge=0)
    is_available: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
