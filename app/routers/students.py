from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.models.enums import UserRole
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.student import (
    StudentProfileCreate,
    StudentProfileRead,
    StudentProfileUpdate,
)

router = APIRouter(prefix="/students", tags=["Students"])


def get_student_or_404(student_id: UUID, session: Session) -> StudentProfile:
    student = session.get(StudentProfile, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    return student


def student_response(student: StudentProfile, session: Session) -> StudentProfileRead:
    user = session.get(User, student.user_id)
    if user is None:
        raise HTTPException(status_code=500, detail="Student user record is missing.")

    return StudentProfileRead(
        id=student.id,
        user_id=student.user_id,
        name=user.name,
        university=student.university,
        skills=student.skills,
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

    student = StudentProfile(**payload.model_dump())
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


@router.patch("/{student_id}", response_model=StudentProfileRead)
def update_student_profile(
    student_id: UUID,
    payload: StudentProfileUpdate,
    session: Session = Depends(get_session),
) -> StudentProfileRead:
    """Update editable profile fields without changing the linked user."""
    student = get_student_or_404(student_id, session)

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field_name, value)
    student.updated_at = datetime.now(timezone.utc)

    session.add(student)
    session.commit()
    session.refresh(student)
    return student_response(student, session)
