from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import WorkPreference

ALLOWED_SKILLS = {
    "GRAPHIC_DESIGN",
    "CANVA",
    "SOCIAL_MEDIA_DESIGN",
    "BRANDING",
    "ILLUSTRATION",
    "CONTENT_WRITING",
    "DIGITAL_MARKETING",
    "DATA_ANALYSIS",
    "VIDEO_EDITING",
    "PROGRAMMING",
    "TRANSLATION",
}


def validate_skills(skills: list[str]) -> list[str]:
    if not skills:
        raise ValueError("At least one skill is required.")

    unknown_skills = set(skills) - ALLOWED_SKILLS
    if unknown_skills:
        names = ", ".join(sorted(unknown_skills))
        raise ValueError(f"Unsupported skill(s): {names}")

    return list(dict.fromkeys(skills))


class StudentProfileCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UUID
    university: str = Field(min_length=1, max_length=150)
    skills: list[str]
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
    skills: list[str] | None = None
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
    name: str
    university: str
    skills: list[str]
    availability: str
    work_preference: WorkPreference
    portfolio_url: str | None
    rating: float
    completed_projects: int
    is_available: bool
    created_at: datetime
    updated_at: datetime
