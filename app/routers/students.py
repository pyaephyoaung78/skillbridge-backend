from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.enums import ProjectStatus, UserRole
from app.models.project import Project
from app.models.student_profile import StudentProfile
from app.models.student_transcript import StudentTranscript
from app.models.user import User
from app.schemas.student import (
    StudentProfileCreate,
    StudentProfileRead,
    StudentProfileUpdate,
)
from app.schemas.match import StudentProjectMatchesRead
from app.services.matching_service import find_ranked_project_matches

router = APIRouter(prefix="/students", tags=["Students"])


def get_student_or_404(student_id: UUID, session: Session) -> StudentProfile:
    student = session.get(StudentProfile, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    return student


def student_response(student: StudentProfile, session: Session) -> StudentProfileRead:
    return StudentProfileRead(
        id=student.id,
        user_id=student.user_id,
        name=student.name,
        university=student.university,
        skills=student.skills,
        technical_skills=student.technical_skills,
        availability=student.availability,
        work_preference=student.work_preference,
        portfolio_url=student.portfolio_url,
        rating=student.rating,
        completed_projects=student.completed_projects,
        is_available=student.is_available,
        created_at=student.created_at,
        updated_at=student.updated_at,
    )


@router.post("", response_model=StudentProfileRead, status_code=status.HTTP_201_CREATED)
def create_student_profile(
    payload: StudentProfileCreate,
    session: Session = Depends(get_session),
) -> StudentProfileRead:
    """Create a profile for a user whose role is STUDENT."""
    user = session.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=422,
            detail="Only a user with the STUDENT role can have a student profile.",
        )

    existing_profile = session.exec(
        select(StudentProfile).where(StudentProfile.user_id == payload.user_id)
    ).first()
    if existing_profile is not None:
        raise HTTPException(
            status_code=409,
            detail="This user already has a student profile.",
        )

    confirmed_name = payload.name
    if payload.transcript_id is not None:
        transcript = session.get(StudentTranscript, payload.transcript_id)
        if transcript is None:
            raise HTTPException(status_code=404, detail="Transcript not found.")
        if transcript.student_user_id != payload.user_id:
            raise HTTPException(
                status_code=403,
                detail="This transcript belongs to another student user.",
            )
        confirmed_name = transcript.extracted_name

    if not confirmed_name:
        raise HTTPException(
            status_code=422,
            detail="Provide a name or a transcript_id with an extracted_name.",
        )

    student_data = payload.model_dump(exclude={"transcript_id", "name"})
    student = StudentProfile(name=confirmed_name, **student_data)
    session.add(student)
    session.commit()
    session.refresh(student)
    return student_response(student, session)


@router.get("/{student_id}", response_model=StudentProfileRead)
def get_student_profile(
    student_id: UUID,
    session: Session = Depends(get_session),
) -> StudentProfileRead:
    """Read one student profile."""
    student = get_student_or_404(student_id, session)
    return student_response(student, session)


@router.get("/{student_id}/matches", response_model=StudentProjectMatchesRead)
def get_student_project_matches(
    student_id: UUID,
    session: Session = Depends(get_session),
) -> StudentProjectMatchesRead:
    """Return OPEN projects recommended for one student; this is not an invitation inbox."""
    student = get_student_or_404(student_id, session)
    projects = session.exec(
        select(Project).where(Project.status == ProjectStatus.OPEN)
    ).all()
    projects_with_owners = [
        (project, owner)
        for project in projects
        if (owner := session.get(User, project.owner_id)) is not None
    ]
    return StudentProjectMatchesRead(
        student_id=student.id,
        projects=find_ranked_project_matches(student, projects_with_owners),
    )


@router.patch("/{student_id}", response_model=StudentProfileRead)
def update_student_profile(
    student_id: UUID,
    payload: StudentProfileUpdate,
    session: Session = Depends(get_session),
) -> StudentProfileRead:
    """Update editable profile fields without changing the linked user."""
    student = get_student_or_404(student_id, session)

    updates = payload.model_dump(exclude_unset=True)
    transcript_id = updates.pop("transcript_id", None)
    if transcript_id is not None:
        transcript = session.get(StudentTranscript, transcript_id)
        if transcript is None:
            raise HTTPException(status_code=404, detail="Transcript not found.")
        if transcript.student_user_id != student.user_id:
            raise HTTPException(
                status_code=403,
                detail="This transcript belongs to another student user.",
            )
        if not transcript.extracted_name:
            raise HTTPException(status_code=422, detail="Transcript has no extracted_name.")
        student.name = transcript.extracted_name

    for field_name, value in updates.items():
        setattr(student, field_name, value)
    student.updated_at = datetime.now(timezone.utc)

    session.add(student)
    session.commit()
    session.refresh(student)
    return student_response(student, session)
