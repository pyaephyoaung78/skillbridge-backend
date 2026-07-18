import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select

from app.config import get_settings
from app.database import get_session
from app.models.enums import UserRole
from app.models.student_transcript import StudentTranscript
from app.models.user import User
from app.schemas.ai import (
    ParseTextRequest,
    ProjectDraft,
    ProjectVoiceDraftResponse,
    StudentProfileDraft,
    TranscriptResponse,
)
from app.schemas.transcript import StudentTranscriptRead
from app.services.ai_service import (
    AIServiceError,
    AIServiceNotConfiguredError,
    parse_project_brief,
    parse_student_profile,
)
from app.services.voice_service import transcribe_burmese_audio

router = APIRouter(tags=["AI and Voice"])
logger = logging.getLogger(__name__)

AUDIO_MIME_TYPES = {
    ".m4a": "audio/mp4",
    ".mp3": "audio/mp3",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".aac": "audio/aac",
    ".aiff": "audio/aiff",
    ".flac": "audio/flac",
}


def provider_error_to_http(error: Exception) -> HTTPException:
    if isinstance(error, AIServiceNotConfiguredError):
        return HTTPException(status_code=503, detail=str(error))
    return HTTPException(status_code=502, detail=str(error))


def get_audio_mime_type(file: UploadFile) -> str:
    """Use the uploaded MIME type, or infer a common audio type from its filename."""
    if file.content_type and file.content_type.startswith("audio/"):
        return file.content_type

    suffix = Path(file.filename or "").suffix.lower()
    mime_type = AUDIO_MIME_TYPES.get(suffix)
    if mime_type is None:
        raise HTTPException(
            status_code=422,
            detail="Please upload an M4A, MP3, WAV, WEBM, OGG, or other audio file.",
        )
    return mime_type


def get_student_user_or_404(student_user_id: UUID, session: Session) -> User:
    user = session.get(User, student_user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Student user not found.")
    if user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=422,
            detail="Transcripts can only be saved for a STUDENT user.",
        )
    return user


def get_project_owner_or_404(owner_id: UUID, session: Session) -> User:
    user = session.get(User, owner_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Project Owner user not found.")
    if user.role != UserRole.PROJECT_OWNER:
        raise HTTPException(
            status_code=422,
            detail="Voice project drafts can only be created for a PROJECT_OWNER user.",
        )
    return user


@router.post("/voice/transcribe", response_model=TranscriptResponse)
async def transcribe_voice(
    file: UploadFile = File(...),
    student_user_id: UUID | None = Form(default=None),
    session: Session = Depends(get_session),
) -> TranscriptResponse:
    """Convert Burmese audio to text and optionally save a nullable student profile draft."""
    mime_type = get_audio_mime_type(file)

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="The audio file is empty.")
    if len(audio_bytes) > get_settings().max_audio_bytes:
        raise HTTPException(status_code=413, detail="Audio file is too large.")

    try:
        transcript = transcribe_burmese_audio(audio_bytes, mime_type)
    except (AIServiceNotConfiguredError, AIServiceError) as error:
        raise provider_error_to_http(error) from error

    # Preserve the original endpoint behavior when no student user ID is sent.
    if student_user_id is None:
        return TranscriptResponse(transcript=transcript)

    get_student_user_or_404(student_user_id, session)
    profile_draft: StudentProfileDraft | None = None
    parsing_status = "TRANSCRIBED_ONLY"
    try:
        profile_draft = parse_student_profile(transcript)
        parsing_status = "PARSED" if not profile_draft.missing_fields else "NEEDS_REVIEW"
    except (AIServiceNotConfiguredError, AIServiceError):
        logger.exception("Could not extract a profile draft from the saved transcript")

    saved_transcript = StudentTranscript(
        student_user_id=student_user_id,
        transcript=transcript,
        extracted_name=profile_draft.name if profile_draft else None,
        extracted_university=profile_draft.university if profile_draft else None,
        extracted_skills=(profile_draft.skills or None) if profile_draft else None,
        extracted_technical_skills=(profile_draft.technical_skills or None) if profile_draft else None,
        extracted_availability=profile_draft.availability if profile_draft else None,
        extracted_work_preference=profile_draft.work_preference if profile_draft else None,
        parsing_status=parsing_status,
    )
    session.add(saved_transcript)
    session.commit()
    session.refresh(saved_transcript)
    return TranscriptResponse(
        transcript=transcript,
        transcription=StudentTranscriptRead.model_validate(saved_transcript),
        profile_draft=profile_draft,
    )


@router.get("/student-users/{student_user_id}/transcripts", response_model=list[StudentTranscriptRead])
def list_student_transcripts(
    student_user_id: UUID,
    session: Session = Depends(get_session),
) -> list[StudentTranscriptRead]:
    """Return a student's saved voice transcripts, newest first."""
    get_student_user_or_404(student_user_id, session)
    transcripts = session.exec(
        select(StudentTranscript)
        .where(StudentTranscript.student_user_id == student_user_id)
        .order_by(StudentTranscript.created_at.desc())
    ).all()
    return [StudentTranscriptRead.model_validate(transcript) for transcript in transcripts]


@router.post("/profiles/parse", response_model=StudentProfileDraft)
def parse_profile(payload: ParseTextRequest) -> StudentProfileDraft:
    """Convert confirmed text into a draft profile. The client must confirm before save."""
    try:
        return parse_student_profile(payload.text)
    except (AIServiceNotConfiguredError, AIServiceError) as error:
        raise provider_error_to_http(error) from error


@router.post("/projects/parse-brief", response_model=ProjectDraft)
def parse_project(payload: ParseTextRequest) -> ProjectDraft:
    """Convert a confirmed brief into a project form draft. It does not save data."""
    try:
        return parse_project_brief(payload.text)
    except (AIServiceNotConfiguredError, AIServiceError) as error:
        raise provider_error_to_http(error) from error


@router.post("/projects/voice-draft", response_model=ProjectVoiceDraftResponse)
async def create_project_voice_draft(
    file: UploadFile = File(...),
    owner_id: UUID = Form(...),
    session: Session = Depends(get_session),
) -> ProjectVoiceDraftResponse:
    """Transcribe owner audio into a read-only project draft before confirmation."""
    get_project_owner_or_404(owner_id, session)
    mime_type = get_audio_mime_type(file)

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="The audio file is empty.")
    if len(audio_bytes) > get_settings().max_audio_bytes:
        raise HTTPException(status_code=413, detail="Audio file is too large.")

    try:
        transcript = transcribe_burmese_audio(audio_bytes, mime_type)
        project_draft = parse_project_brief(transcript)
    except (AIServiceNotConfiguredError, AIServiceError) as error:
        raise provider_error_to_http(error) from error

    return ProjectVoiceDraftResponse(
        transcript=transcript,
        project_draft=project_draft,
    )
