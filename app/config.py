import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Local development reads secrets from .env; deployment can use real environment variables.
load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    gemini_model: str
    gemini_audio_model: str
    max_audio_bytes: int


def get_settings() -> Settings:
    """Read optional AI-service configuration without exposing secrets in code."""
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        gemini_audio_model=os.getenv("GEMINI_AUDIO_MODEL", "gemini-2.5-flash"),
        max_audio_bytes=int(os.getenv("MAX_AUDIO_BYTES", str(10 * 1024 * 1024))),
    )
