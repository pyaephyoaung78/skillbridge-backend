from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.models.enums import InvitationStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Invitation(SQLModel, table=True):
    """An owner's offer to one selected student for one project."""

    __tablename__ = "invitations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    project_id: UUID = Field(index=True, foreign_key="projects.id")
    student_id: UUID = Field(index=True, foreign_key="student_profiles.id")
    status: InvitationStatus = Field(default=InvitationStatus.PENDING)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    responded_at: datetime | None = Field(default=None, nullable=True)
