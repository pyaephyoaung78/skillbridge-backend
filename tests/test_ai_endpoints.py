from fastapi.testclient import TestClient

from app.routers import ai
from app.schemas.ai import ProjectDraft, StudentProfileDraft
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


def test_ai_endpoints_show_clear_setup_error_when_not_configured(monkeypatch) -> None:
    def not_configured(_: str) -> StudentProfileDraft:
        raise ai.AIServiceNotConfiguredError("GEMINI_API_KEY is not configured.")

    monkeypatch.setattr(ai, "parse_student_profile", not_configured)
    with TestClient(app) as client:
        response = client.post("/profiles/parse", json={"text": "profile text"})

    assert response.status_code == 503
    assert response.json()["detail"] == "GEMINI_API_KEY is not configured."
