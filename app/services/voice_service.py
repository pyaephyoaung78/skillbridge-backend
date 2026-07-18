import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from app.config import get_settings
from app.services.ai_service import AIServiceError, AIServiceNotConfiguredError

logger = logging.getLogger(__name__)

# Gemini accepts these formats directly. M4A and WebM are common browser/phone
# recording formats, but Gemini does not accept their MIME types directly.
DIRECT_GEMINI_MIME_TYPES = {
    "audio/wav": "audio/wav",
    "audio/x-wav": "audio/wav",
    "audio/wave": "audio/wav",
    "audio/mp3": "audio/mp3",
    "audio/mpeg": "audio/mp3",
    "audio/aiff": "audio/aiff",
    "audio/aac": "audio/aac",
    "audio/ogg": "audio/ogg",
    "audio/flac": "audio/flac",
}

CONVERT_TO_WAV_MIME_TYPES = {
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/webm": ".webm",
}


def _convert_to_wav(audio_bytes: bytes, input_suffix: str) -> bytes:
    """Convert a browser/phone recording to a Gemini-supported WAV file."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        raise AIServiceError(
            "The server needs FFmpeg to transcribe M4A or WebM recordings. "
            "Install it with: sudo apt install -y ffmpeg"
        )

    try:
        with tempfile.TemporaryDirectory(prefix="skillbridge-audio-") as directory:
            input_path = Path(directory) / f"recording{input_suffix}"
            output_path = Path(directory) / "recording.wav"
            input_path.write_bytes(audio_bytes)

            result = subprocess.run(
                [
                    ffmpeg_path,
                    "-y",
                    "-i",
                    str(input_path),
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    str(output_path),
                ],
                capture_output=True,
                check=False,
                timeout=30,
            )
            if result.returncode != 0 or not output_path.exists():
                logger.warning("FFmpeg could not convert uploaded audio: %s", result.stderr.decode(errors="replace"))
                raise AIServiceError(
                    "The audio file could not be read. Record it again or upload MP3, WAV, AAC, OGG, or FLAC."
                )
            return output_path.read_bytes()
    except subprocess.TimeoutExpired as error:
        raise AIServiceError("Audio conversion took too long. Upload a shorter recording.") from error
    except OSError as error:
        raise AIServiceError("The server could not convert the audio file.") from error


def prepare_audio_for_gemini(audio_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """Return audio bytes and a MIME type that Gemini supports."""
    normalized_mime_type = mime_type.lower().split(";", maxsplit=1)[0].strip()
    direct_mime_type = DIRECT_GEMINI_MIME_TYPES.get(normalized_mime_type)
    if direct_mime_type is not None:
        return audio_bytes, direct_mime_type

    input_suffix = CONVERT_TO_WAV_MIME_TYPES.get(normalized_mime_type)
    if input_suffix is not None:
        return _convert_to_wav(audio_bytes, input_suffix), "audio/wav"

    raise AIServiceError(
        "Unsupported audio format. Upload M4A, MP3, WAV, WEBM, AAC, OGG, AIFF, or FLAC."
    )


def transcribe_burmese_audio(audio_bytes: bytes, mime_type: str) -> str:
    """Transcribe a completed short Burmese recording with Gemini audio input."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise AIServiceNotConfiguredError("GEMINI_API_KEY is not configured.")

    try:
        from google import genai
        from google.genai import types

        gemini_audio_bytes, gemini_mime_type = prepare_audio_for_gemini(audio_bytes, mime_type)
        
        # Initialize the client with your Cloudflare Worker proxy endpoint
        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={
                "base_url": "https://gemini-proxy35.aungmkyaw03.workers.dev"
            }
        )
        
        response = client.models.generate_content(
            model=settings.gemini_audio_model,
            contents=[
                (
                    "Transcribe only the spoken words in this audio. "
                    "The primary language is Burmese (Myanmar). "
                    "Return the transcript in Burmese script where appropriate. "
                    "Keep technical terms, software names, skill names, job titles, "
                    "and English words in English; do not translate or transliterate them into Burmese. "
                    "Examples: Graphic Design, Canva, Social Media, UI/UX, Python, "
                    "Digital Marketing, and Video Editing. "
                    "Do not translate, summarize, explain, add timestamps, or add labels."
                ),
                types.Part.from_bytes(data=gemini_audio_bytes, mime_type=gemini_mime_type),
            ],
        )
    except Exception as error:
        logger.exception("Gemini transcription request failed")
        if isinstance(error, AIServiceError):
            raise
        raise AIServiceError("Gemini could not transcribe this audio.") from error

    transcript = (response.text or "").strip()
    if not transcript:
        raise AIServiceError("No speech was detected in the audio.")
    return transcript
