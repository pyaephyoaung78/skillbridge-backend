from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import InvitationStatus, ProjectStatus, WorkType


class InvitationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_id: UUID
    project_id: UUID
    student_id: UUID


class InvitationRespond(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: UUID


class InvitationRead(BaseModel):
    id: UUID
    project_id: UUID
    student_id: UUID
    student_name: str
    owner_name: str
    project_title: str
    required_skills: list[str]
    deadline: date
    work_type: WorkType
    budget_mmk: int
    project_status: ProjectStatus
    status: InvitationStatus
    created_at: datetime
    responded_at: datetime | None
