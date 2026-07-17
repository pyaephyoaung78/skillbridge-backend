import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Local development reads secrets from .env; deployment can use real environment variables.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    google_cloud_project: str | None
    speech_region: str
    speech_model: str
    gemini_api_key: str | None
    gemini_model: str
    max_audio_bytes: int


def get_settings() -> Settings:
    """Read optional AI-service configuration without exposing secrets in code."""
    return Settings(
        google_cloud_project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        speech_region=os.getenv("GOOGLE_SPEECH_REGION", "asia-southeast1"),
        speech_model=os.getenv("GOOGLE_SPEECH_MODEL", "chirp_2"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        max_audio_bytes=int(os.getenv("MAX_AUDIO_BYTES", str(10 * 1024 * 1024))),
    )
