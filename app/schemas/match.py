from uuid import UUID

from pydantic import BaseModel

from app.models.enums import WorkPreference


class MatchCandidateRead(BaseModel):
    student_id: UUID
    name: str
    skills: list[str]
    availability: str
    work_preference: WorkPreference
    portfolio_url: str | None
    rating: float
    completed_projects: int
    matched_skills: list[str]
    score: int
    explanation: str
    priority_rank: int | None = None


class ProjectMatchesRead(BaseModel):
    project_id: UUID
    candidates: list[MatchCandidateRead]


class MatchRecommendationRead(BaseModel):
    student_id: UUID
    priority_rank: int
    score: int
    recommendation: str
    source: str


class ProjectRecommendationsRead(BaseModel):
    project_id: UUID
    recommendations: list[MatchRecommendationRead]
