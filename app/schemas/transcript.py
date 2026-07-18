from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import WorkPreference


class StudentTranscriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_user_id: UUID
    transcript: str
    extracted_name: str | None
    extracted_university: str | None
    extracted_skills: list[str] | None
    extracted_technical_skills: list[str] | None
    extracted_availability: str | None
    extracted_work_preference: WorkPreference | None
    parsing_status: str
    created_at: datetime
