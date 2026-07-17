from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import validate_skills
from app.models.enums import ProjectStatus, WorkType


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    owner_id: UUID
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=2_000)
    role: str = Field(min_length=1, max_length=100)
    required_skills: list[str]
    required_availability: str = Field(min_length=1, max_length=50)
    deadline: date
    work_type: WorkType
    budget_mmk: int = Field(ge=1)

    @field_validator("required_skills")
    @classmethod
    def required_skills_must_be_allowed(cls, skills: list[str]) -> list[str]:
        return validate_skills(skills)

    @field_validator("deadline")
    @classmethod
    def deadline_must_not_be_in_the_past(cls, deadline: date) -> date:
        if deadline < date.today():
            raise ValueError("Deadline cannot be in the past.")
        return deadline


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    owner_name: str
    title: str
    description: str
    role: str
    required_skills: list[str]
    required_availability: str
    deadline: date
    work_type: WorkType
    compensation_type: str
    budget_mmk: int
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
