from fastapi.testclient import TestClient

from app.routers import ai
from app.schemas.ai import ProjectDraft, StudentProfileDraft
from app.services import voice_service
from main import app


def test_profile_parse_returns_a_draft_without_saving(monkeypatch) -> None:
    def fake_parse(_: str) -> StudentProfileDraft:
        return StudentProfileDraft(
            name="မောင်မောင်",
            university="University of Yangon",
            skills=["GRAPHIC_DESIGN", "CANVA"],
            availability="WEEKDAY_EVENINGS",
            work_preference="REMOTE",
        )

    monkeypatch.setattr(ai, "parse_student_profile", fake_parse)
    with TestClient(app) as client:
        response = client.post(
            "/profiles/parse",
            json={"text": "ကျွန်တော် Graphic Design နဲ့ Canva တတ်ပါတယ်"},
        )

    assert response.status_code == 200
    assert response.json()["skills"] == ["GRAPHIC_DESIGN", "CANVA"]


def test_project_parse_returns_a_draft_without_saving(monkeypatch) -> None:
    def fake_parse(_: str) -> ProjectDraft:
        return ProjectDraft(
            title="Tech Event Social Media Design",
            description="Create social-media posters.",
            role="GRAPHIC_DESIGNER",
            required_skills=["GRAPHIC_DESIGN", "CANVA"],
            required_availability="WEEKDAY_EVENINGS",
            deadline="2026-07-24",
            work_type="REMOTE",
            budget_mmk=60_000,
        )

    monkeypatch.setattr(ai, "parse_project_brief", fake_parse)
    with TestClient(app) as client:
        response = client.post(
            "/projects/parse-brief",
            json={"text": "Friday မတိုင်ခင် poster ဆွဲပေးမယ့် designer လိုတယ်"},
        )

    assert response.status_code == 200
    assert response.json()["budget_mmk"] == 60_000


def test_voice_endpoint_rejects_a_non_audio_upload() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/voice/transcribe",
            files={"file": ("notes.txt", b"not audio", "text/plain")},
        )

    assert response.status_code == 422


def test_voice_endpoint_returns_a_burmese_transcript(monkeypatch) -> None:
    def fake_transcribe(audio_bytes: bytes, mime_type: str) -> str:
        assert audio_bytes == b"audio bytes"
        assert mime_type == "audio/mp4"
        return "Graphic Design နဲ့ Canva တတ်ပါတယ်။"

    monkeypatch.setattr(ai, "transcribe_burmese_audio", fake_transcribe)
    with TestClient(app) as client:
        response = client.post(
            "/voice/transcribe",
            files={"file": ("profile.m4a", b"audio bytes", "audio/mp4")},
        )

    assert response.status_code == 200
    assert response.json()["transcript"] == "Graphic Design နဲ့ Canva တတ်ပါတယ်။"


def test_m4a_audio_is_converted_to_wav_for_gemini(monkeypatch) -> None:
    def fake_convert(audio_bytes: bytes, input_suffix: str) -> bytes:
        assert audio_bytes == b"m4a bytes"
        assert input_suffix == ".m4a"
        return b"wav bytes"

    monkeypatch.setattr(voice_service, "_convert_to_wav", fake_convert)

    audio_bytes, mime_type = voice_service.prepare_audio_for_gemini(
        b"m4a bytes", "audio/mp4"
    )

    assert audio_bytes == b"wav bytes"
    assert mime_type == "audio/wav"


def test_mp3_audio_uses_gemini_supported_mime_type() -> None:
    audio_bytes, mime_type = voice_service.prepare_audio_for_gemini(
        b"mp3 bytes", "audio/mpeg"
    )

    assert audio_bytes == b"mp3 bytes"
    assert mime_type == "audio/mp3"


def test_ai_endpoints_show_clear_setup_error_when_not_configured(monkeypatch) -> None:
    def not_configured(_: str) -> StudentProfileDraft:
        raise ai.AIServiceNotConfiguredError("GEMINI_API_KEY is not configured.")

    monkeypatch.setattr(ai, "parse_student_profile", not_configured)
    with TestClient(app) as client:
        response = client.post("/profiles/parse", json={"text": "profile text"})

    assert response.status_code == 503
    assert response.json()["detail"] == "GEMINI_API_KEY is not configured."
