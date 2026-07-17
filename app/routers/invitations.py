from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.enums import InvitationStatus, ProjectStatus, UserRole
from app.models.invitation import Invitation
from app.models.project import Project
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.invitation import InvitationCreate, InvitationRead, InvitationRespond
from app.services.matching_service import student_is_eligible_for_project

router = APIRouter(tags=["Invitations"])


def get_invitation_or_404(invitation_id: UUID, session: Session) -> Invitation:
    invitation = session.get(Invitation, invitation_id)
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found.")
    return invitation


def get_project_or_404(project_id: UUID, session: Session) -> Project:
    project = session.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


def get_student_or_404(student_id: UUID, session: Session) -> StudentProfile:
    student = session.get(StudentProfile, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    return student


def invitation_response(invitation: Invitation, session: Session) -> InvitationRead:
    project = get_project_or_404(invitation.project_id, session)
    student = get_student_or_404(invitation.student_id, session)
    student_user = session.get(User, student.user_id)
    owner = session.get(User, project.owner_id)
    if student_user is None or owner is None:
        raise HTTPException(status_code=500, detail="Related user record is missing.")

    return InvitationRead(
        id=invitation.id,
        project_id=project.id,
        student_id=student.id,
        student_name=student_user.name,
        owner_name=owner.name,
        project_title=project.title,
        required_skills=project.required_skills,
        deadline=project.deadline,
        work_type=project.work_type,
        budget_mmk=project.budget_mmk,
        project_status=project.status,
        status=invitation.status,
        created_at=invitation.created_at,
        responded_at=invitation.responded_at,
    )


def validate_owner_for_project(owner_id: UUID, project: Project, session: Session) -> None:
    owner = session.get(User, owner_id)
    if owner is None:
        raise HTTPException(status_code=404, detail="Project Owner user not found.")
    if owner.role != UserRole.PROJECT_OWNER or project.owner_id != owner_id:
        raise HTTPException(
            status_code=403,
            detail="Only the owner of this project can send an invitation.",
        )


def ensure_project_has_no_active_invitation(project_id: UUID, session: Session) -> None:
    invitations = session.exec(
        select(Invitation).where(Invitation.project_id == project_id)
    ).all()
    has_active_invitation = any(
        invitation.status in {InvitationStatus.PENDING, InvitationStatus.ACCEPTED}
        for invitation in invitations
    )
    if has_active_invitation:
        raise HTTPException(
            status_code=409,
            detail="This project already has a pending or accepted invitation.",
        )


@router.post(
    "/invitations",
    response_model=InvitationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    payload: InvitationCreate,
    session: Session = Depends(get_session),
) -> InvitationRead:
    """Allow an owner to invite one eligible student for an OPEN project."""
    project = get_project_or_404(payload.project_id, session)
    validate_owner_for_project(payload.owner_id, project, session)
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=409, detail="Only OPEN projects can send invitations.")

    student = get_student_or_404(payload.student_id, session)
    if not student_is_eligible_for_project(student, project):
        raise HTTPException(
            status_code=422,
            detail="This student is not eligible for the project invitation.",
        )
    ensure_project_has_no_active_invitation(project.id, session)

    invitation = Invitation(project_id=project.id, student_id=student.id)
    session.add(invitation)
    session.commit()
    session.refresh(invitation)
    return invitation_response(invitation, session)


@router.get("/students/{student_id}/invitations", response_model=list[InvitationRead])
def list_student_invitations(
    student_id: UUID,
    session: Session = Depends(get_session),
) -> list[InvitationRead]:
    """Return a student's invitation inbox, newest first."""
    get_student_or_404(student_id, session)
    invitations = session.exec(
        select(Invitation)
        .where(Invitation.student_id == student_id)
        .order_by(Invitation.created_at.desc())
    ).all()
    return [invitation_response(invitation, session) for invitation in invitations]


@router.post("/invitations/{invitation_id}/accept", response_model=InvitationRead)
def accept_invitation(
    invitation_id: UUID,
    payload: InvitationRespond,
    session: Session = Depends(get_session),
) -> InvitationRead:
    """Accept one pending invitation and fill its project."""
    invitation = get_invitation_or_404(invitation_id, session)
    if invitation.student_id != payload.student_id:
        raise HTTPException(status_code=403, detail="This invitation belongs to another student.")
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=409, detail="Only a pending invitation can be accepted.")

    project = get_project_or_404(invitation.project_id, session)
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=409, detail="This project is no longer OPEN.")

    accepted_invitation = session.exec(
        select(Invitation).where(
            Invitation.project_id == project.id,
            Invitation.status == InvitationStatus.ACCEPTED,
        )
    ).first()
    if accepted_invitation is not None:
        raise HTTPException(status_code=409, detail="This project already has an accepted student.")

    now = datetime.now(timezone.utc)
    invitation.status = InvitationStatus.ACCEPTED
    invitation.responded_at = now
    project.status = ProjectStatus.FILLED
    project.updated_at = now
    session.add(invitation)
    session.add(project)
    session.commit()
    session.refresh(invitation)
    return invitation_response(invitation, session)


@router.post("/invitations/{invitation_id}/decline", response_model=InvitationRead)
def decline_invitation(
    invitation_id: UUID,
    payload: InvitationRespond,
    session: Session = Depends(get_session),
) -> InvitationRead:
    """Decline a pending invitation and keep the project OPEN for another choice."""
    invitation = get_invitation_or_404(invitation_id, session)
    if invitation.student_id != payload.student_id:
        raise HTTPException(status_code=403, detail="This invitation belongs to another student.")
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(status_code=409, detail="Only a pending invitation can be declined.")

    invitation.status = InvitationStatus.DECLINED
    invitation.responded_at = datetime.now(timezone.utc)
    session.add(invitation)
    session.commit()
    session.refresh(invitation)
    return invitation_response(invitation, session)
