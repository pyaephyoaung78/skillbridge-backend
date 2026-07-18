from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.enums import ProjectStatus, UserRole
from app.models.project import Project
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.match import (
    MatchRecommendationRead,
    ProjectMatchesRead,
    ProjectRecommendationsRead,
)
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.ai_service import AIServiceError, AIServiceNotConfiguredError, generate_match_recommendations
from app.services.matching_service import find_ranked_matches

router = APIRouter(prefix="/projects", tags=["Projects"])
owner_router = APIRouter(prefix="/owners", tags=["Projects"])
logger = logging.getLogger(__name__)


def get_project_or_404(project_id: UUID, session: Session) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


def get_owner_or_404(owner_id: UUID, session: Session) -> User:
    owner = session.get(User, owner_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="Project Owner user not found.")
    if owner.role != UserRole.PROJECT_OWNER:
        raise HTTPException(
            status_code=422,
            detail="Only a user with the PROJECT_OWNER role can manage projects.",
        )
    return owner


def project_response(project: Project, session: Session) -> ProjectRead:
    owner = session.get(User, project.owner_id)
    if owner is None:
        raise HTTPException(status_code=500, detail="Project Owner user record is missing.")

    return ProjectRead(
        id=project.id,
        owner_id=project.owner_id,
        owner_name=owner.name,
        title=project.title,
        description=project.description,
        role=project.role,
        required_skills=project.required_skills,
        required_availability=project.required_availability,
        deadline=project.deadline,
        work_type=project.work_type,
        compensation_type=project.compensation_type,
        budget_mmk=project.budget_mmk,
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    session: Session = Depends(get_session),
) -> ProjectRead:
    """Create one paid project for one future student invitation."""
    get_owner_or_404(payload.owner_id, session)

    # These values are controlled by the backend, not an editable Flutter form.
    project = Project(
        **payload.model_dump(),
        compensation_type="PAID",
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project_response(project, session)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, session: Session = Depends(get_session)) -> ProjectRead:
    """Read one project and its current status."""
    project = get_project_or_404(project_id, session)
    return project_response(project, session)


@router.get("/{project_id}/matches", response_model=ProjectMatchesRead)
def get_project_matches(
    project_id: UUID,
    session: Session = Depends(get_session),
) -> ProjectMatchesRead:
    """Return every eligible student, with the highest three marked as priorities."""
    project = get_project_or_404(project_id, session)
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(
            status_code=409,
            detail="Matches are available only while a project is OPEN.",
        )

    students = session.exec(select(StudentProfile)).all()
    students_with_users = [
        (student, user)
        for student in students
        if (user := session.get(User, student.user_id)) is not None
    ]

    return ProjectMatchesRead(
        project_id=project.id,
        candidates=find_ranked_matches(project, students_with_users),
    )


@router.post("/{project_id}/recommendations", response_model=ProjectRecommendationsRead)
def create_project_recommendations(
    project_id: UUID,
    session: Session = Depends(get_session),
) -> ProjectRecommendationsRead:
    """Generate AI explanations for the top three; fall back to factual rule explanations."""
    project = get_project_or_404(project_id, session)
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(
            status_code=409,
            detail="Recommendations are available only while a project is OPEN.",
        )

    students = session.exec(select(StudentProfile)).all()
    students_with_users = [
        (student, user)
        for student in students
        if (user := session.get(User, student.user_id)) is not None
    ]
    priority_candidates = find_ranked_matches(project, students_with_users)[:3]
    if not priority_candidates:
        return ProjectRecommendationsRead(project_id=project.id, recommendations=[])

    fallback = {
        candidate.student_id: MatchRecommendationRead(
            student_id=candidate.student_id,
            priority_rank=candidate.priority_rank or 0,
            score=candidate.score,
            recommendation=candidate.explanation,
            source="RULE_BASED_FALLBACK",
        )
        for candidate in priority_candidates
    }

    try:
        ai_recommendations = generate_match_recommendations(project, priority_candidates)
    except (AIServiceNotConfiguredError, AIServiceError):
        logger.exception("Could not generate AI match recommendations; using rule-based fallback")
        return ProjectRecommendationsRead(
            project_id=project.id,
            recommendations=list(fallback.values()),
        )

    for ai_recommendation in ai_recommendations:
        fallback_recommendation = fallback.get(ai_recommendation.student_id)
        if fallback_recommendation is not None:
            fallback[ai_recommendation.student_id] = fallback_recommendation.model_copy(
                update={
                    "recommendation": ai_recommendation.recommendation,
                    "source": "AI",
                }
            )

    return ProjectRecommendationsRead(
        project_id=project.id,
        recommendations=[fallback[candidate.student_id] for candidate in priority_candidates],
    )


@owner_router.get("/{owner_id}/projects", response_model=list[ProjectRead])
def list_owner_projects(owner_id: UUID, session: Session = Depends(get_session)) -> list[ProjectRead]:
    """Return an owner's projects, newest first, for the owner dashboard."""
    get_owner_or_404(owner_id, session)
    projects = session.exec(
        select(Project)
        .where(Project.owner_id == owner_id)
        .order_by(Project.created_at.desc())
    ).all()
    return [project_response(project, session) for project in projects]
