from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel

from app.models.enums import ProjectStatus, WorkType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(SQLModel, table=True):
    """A paid short-term project that can be filled by one student."""

    __tablename__ = "projects"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(index=True, foreign_key="users.id")
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=2_000)
    role: str = Field(min_length=1, max_length=100)
    required_skills: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )
    required_technical_skills: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    required_availability: str = Field(min_length=1, max_length=50)
    deadline: date
    work_type: WorkType
    compensation_type: str = Field(default="PAID", max_length=20)
    budget_mmk: int = Field(ge=1)
    status: ProjectStatus = Field(default=ProjectStatus.OPEN)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
