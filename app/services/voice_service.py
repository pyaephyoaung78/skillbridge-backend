from app.config import get_settings
from app.services.ai_service import AIServiceError, AIServiceNotConfiguredError


def transcribe_burmese_audio(audio_bytes: bytes, mime_type: str) -> str:
    """Transcribe a completed short Burmese recording with Gemini audio input."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise AIServiceNotConfiguredError("GEMINI_API_KEY is not configured.")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_audio_model,
            contents=[
                (
                    "Transcribe only the spoken words in this audio. "
                    "The primary language is Burmese (Myanmar). "
                    "Return the transcript in Burmese script where appropriate. "
                    "Do not translate, summarize, explain, add timestamps, or add labels."
                ),
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            ],
        )
    except Exception as error:
        raise AIServiceError("Gemini could not transcribe this audio.") from error

    transcript = (response.text or "").strip()
    if not transcript:
        raise AIServiceError("No speech was detected in the audio.")
    return transcript
