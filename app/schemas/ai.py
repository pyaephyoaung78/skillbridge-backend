from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import ALLOWED_SKILLS
from app.models.enums import WorkPreference, WorkType


class ParseTextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    text: str = Field(min_length=1, max_length=5_000)


class TranscriptResponse(BaseModel):
    transcript: str
    language_code: str = "my-MM"


def validate_draft_skills(skills: list[str]) -> list[str]:
    unknown_skills = set(skills) - ALLOWED_SKILLS
    if unknown_skills:
        names = ", ".join(sorted(unknown_skills))
        raise ValueError(f"Unsupported skill(s): {names}")
    return list(dict.fromkeys(skills))


class StudentProfileDraft(BaseModel):
    name: str | None = None
    university: str | None = None
    skills: list[str] = Field(default_factory=list)
    availability: str | None = None
    work_preference: WorkPreference | None = None
    missing_fields: list[str] = Field(default_factory=list)

    @field_validator("skills")
    @classmethod
    def draft_skills_must_be_allowed(cls, skills: list[str]) -> list[str]:
        return validate_draft_skills(skills)


class ProjectDraft(BaseModel):
    title: str | None = None
    description: str | None = None
    role: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    required_availability: str | None = None
    deadline: date | None = None
    work_type: WorkType | None = None
    budget_mmk: int | None = Field(default=None, ge=1)
    missing_fields: list[str] = Field(default_factory=list)

    @field_validator("required_skills")
    @classmethod
    def required_draft_skills_must_be_allowed(cls, skills: list[str]) -> list[str]:
        return validate_draft_skills(skills)


class MatchRecommendationDraft(BaseModel):
    student_id: UUID
    recommendation: str = Field(min_length=1, max_length=300)


class MatchRecommendationsDraft(BaseModel):
    recommendations: list[MatchRecommendationDraft]
