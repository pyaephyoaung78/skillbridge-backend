from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import WorkPreference, WorkType


class MatchCandidateRead(BaseModel):
    student_id: UUID
    name: str
    skills: list[str]
    technical_skills: list[str]
    availability: str
    work_preference: WorkPreference
    portfolio_url: str | None
    rating: float
    completed_projects: int
    matched_skills: list[str]
    matched_technical_skills: list[str]
    score: int
    explanation: str
    priority_rank: int | None = None


class ProjectMatchesRead(BaseModel):
    project_id: UUID
    candidates: list[MatchCandidateRead]


class ProjectMatchRead(BaseModel):
    project_id: UUID
    owner_id: UUID
    owner_name: str
    title: str | None
    description: str
    role: str
    required_skills: list[str]
    required_technical_skills: list[str]
    required_availability: str
    deadline: date
    work_type: WorkType
    budget_mmk: int
    matched_skills: list[str]
    matched_technical_skills: list[str]
    score: int
    explanation: str
    priority_rank: int | None = None


class StudentProjectMatchesRead(BaseModel):
    student_id: UUID
    projects: list[ProjectMatchRead]


class MatchRecommendationRead(BaseModel):
    student_id: UUID
    priority_rank: int
    score: int
    recommendation: str
    source: str


class ProjectRecommendationsRead(BaseModel):
    project_id: UUID
    recommendations: list[MatchRecommendationRead]
