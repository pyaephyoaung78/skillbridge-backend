from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import validate_skills
from app.models.enums import WorkPreference


class StudentProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UUID
    transcript_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=150)
    university: str = Field(min_length=1, max_length=150)
    skills: list[str]
    technical_skills: list[str] = Field(default_factory=list)
    availability: str = Field(min_length=1, max_length=50)
    work_preference: WorkPreference
    portfolio_url: str | None = Field(default=None, max_length=500)
    is_available: bool = True

    @field_validator("skills")
    @classmethod
    def skills_must_be_allowed(cls, skills: list[str]) -> list[str]:
        return validate_skills(skills)


class StudentProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    university: str | None = Field(default=None, min_length=1, max_length=150)
    transcript_id: UUID | None = None
    skills: list[str] | None = None
    technical_skills: list[str] | None = None
    availability: str | None = Field(default=None, min_length=1, max_length=50)
    work_preference: WorkPreference | None = None
    portfolio_url: str | None = Field(default=None, max_length=500)
    is_available: bool | None = None

    @field_validator("skills")
    @classmethod
    def updated_skills_must_be_allowed(cls, skills: list[str] | None) -> list[str] | None:
        return validate_skills(skills) if skills is not None else skills


class StudentProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str | None
    university: str
    skills: list[str]
    technical_skills: list[str] | None
    availability: str
    work_preference: WorkPreference
    portfolio_url: str | None
    rating: float
    completed_projects: int
    is_available: bool
    created_at: datetime
    updated_at: datetime
