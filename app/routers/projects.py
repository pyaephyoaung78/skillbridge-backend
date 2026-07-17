from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.enums import UserRole
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead

router = APIRouter(prefix="/projects", tags=["Projects"])
owner_router = APIRouter(prefix="/owners", tags=["Projects"])


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
