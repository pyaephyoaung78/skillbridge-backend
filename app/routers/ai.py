from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import get_settings
from app.schemas.ai import (
    ParseTextRequest,
    ProjectDraft,
    StudentProfileDraft,
    TranscriptResponse,
)
from app.services.ai_service import (
    AIServiceError,
    AIServiceNotConfiguredError,
    parse_project_brief,
    parse_student_profile,
)
from app.services.voice_service import transcribe_burmese_audio

router = APIRouter(tags=["AI and Voice"])

AUDIO_MIME_TYPES = {
    ".m4a": "audio/mp4",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
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


@router.post("/voice/transcribe", response_model=TranscriptResponse)
async def transcribe_voice(file: UploadFile = File(...)) -> TranscriptResponse:
    """Convert a short Burmese recording to editable text. It does not save data."""
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
    return TranscriptResponse(transcript=transcript)


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
