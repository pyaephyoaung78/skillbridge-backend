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

    # Voice agent မထုတ်နိုင်လျှင် null ခွင့်ပြုသော fields
    title: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=2_000)
    role: str | None = Field(default=None, max_length=100)

    required_skills: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )
    required_technical_skills: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
    )

    required_availability: str | None = Field(default=None, max_length=50)
    deadline: date | None = Field(default=None)
    work_type: WorkType | None = Field(default=None)
    budget_mmk: int | None = Field(default=None, ge=1)

    # System-managed fields
    compensation_type: str = Field(default="PAID", max_length=20)
    status: ProjectStatus = Field(default=ProjectStatus.OPEN)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
