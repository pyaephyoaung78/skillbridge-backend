from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from app.database import get_session
from app.routers import projects
from main import app


@pytest.fixture
def client(tmp_path) -> Generator[TestClient, None, None]:
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'skillbridge-test.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(test_engine)

    def get_test_session() -> Generator[Session, None, None]:
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_user(client: TestClient, name: str, role: str) -> str:
    response = client.post("/users", json={"name": name, "role": role})
    assert response.status_code == 201
    return response.json()["id"]


def create_student(
    client: TestClient,
    *,
    name: str,
    skills: list[str],
    availability: str,
    work_preference: str = "REMOTE",
    technical_skills: list[str] | None = None,
    portfolio_url: str | None = None,
    is_available: bool = True,
) -> str:
    user_id = create_user(client, name, "STUDENT")
    response = client.post(
        "/students",
        json={
            "user_id": user_id,
            "name": name,
            "university": "University of Yangon",
            "skills": skills,
            "technical_skills": technical_skills or [],
            "availability": availability,
            "work_preference": work_preference,
            "portfolio_url": portfolio_url,
            "is_available": is_available,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_project(
    client: TestClient,
    *,
    required_technical_skills: list[str] | None = None,
) -> str:
    owner_id = create_user(client, "Tech Event Club", "PROJECT_OWNER")
    response = client.post(
        "/projects",
        json={
            "owner_id": owner_id,
            "title": "Tech Event Social Media Design",
            "description": "Create social-media posters for a university tech event.",
            "role": "GRAPHIC_DESIGNER",
            "required_skills": ["GRAPHIC_DESIGN", "CANVA"],
            "required_technical_skills": required_technical_skills or [],
            "required_availability": "WEEKDAY_EVENINGS",
            "deadline": (date.today() + timedelta(days=7)).isoformat(),
            "work_type": "REMOTE",
            "budget_mmk": 60_000,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_matches_are_filtered_scored_and_prioritize_the_top_three(client: TestClient) -> None:
    create_student(
        client,
        name="မေသဇင်",
        skills=["GRAPHIC_DESIGN", "CANVA"],
        availability="WEEKDAY_EVENINGS",
        portfolio_url="https://www.behance.net/may",
    )
    create_student(
        client,
        name="ကိုမင်း",
        skills=["GRAPHIC_DESIGN", "CANVA"],
        availability="WEEKENDS",
        portfolio_url="https://www.behance.net/min",
    )
    create_student(
        client,
        name="အိမ့်ပိုး",
        skills=["GRAPHIC_DESIGN"],
        availability="WEEKDAY_EVENINGS",
    )
    create_student(
        client,
        name="သီဟ",
        skills=["GRAPHIC_DESIGN"],
        availability="WEEKENDS",
    )
    create_student(
        client,
        name="မခင်",
        skills=["CONTENT_WRITING"],
        availability="WEEKDAY_EVENINGS",
    )
    create_student(
        client,
        name="ကိုအောင်",
        skills=["GRAPHIC_DESIGN", "CANVA"],
        availability="WEEKDAY_EVENINGS",
        is_available=False,
    )

    project_id = create_project(client)
    response = client.get(f"/projects/{project_id}/matches")

    assert response.status_code == 200
    candidates = response.json()["candidates"]
    assert [candidate["name"] for candidate in candidates] == [
        "မေသဇင်",
        "ကိုမင်း",
        "အိမ့်ပိုး",
        "သီဟ",
    ]
    assert [candidate["score"] for candidate in candidates] == [100, 75, 68, 43]
    assert [candidate["priority_rank"] for candidate in candidates] == [1, 2, 3, None]
    assert candidates[0]["matched_skills"] == ["GRAPHIC_DESIGN", "CANVA"]
    assert candidates[0]["matched_technical_skills"] == []
    assert candidates[0]["explanation"]


def test_technical_skills_are_used_for_project_matching(client: TestClient) -> None:
    create_student(
        client,
        name="Figma Designer",
        skills=["GRAPHIC_DESIGN"],
        technical_skills=["figma", "Adobe Photoshop"],
        availability="WEEKDAY_EVENINGS",
    )
    create_student(
        client,
        name="Canva Designer",
        skills=["GRAPHIC_DESIGN"],
        technical_skills=["Canva"],
        availability="WEEKDAY_EVENINGS",
    )

    project_id = create_project(client, required_technical_skills=["Figma"])
    response = client.get(f"/projects/{project_id}/matches")

    assert response.status_code == 200
    candidates = response.json()["candidates"]
    assert [candidate["name"] for candidate in candidates] == ["Figma Designer"]
    assert candidates[0]["matched_technical_skills"] == ["Figma"]
    assert candidates[0]["technical_skills"] == ["figma", "Adobe Photoshop"]


def test_student_can_view_ranked_matching_open_projects(client: TestClient) -> None:
    student_id = create_student(
        client,
        name="Figma Designer",
        skills=["GRAPHIC_DESIGN", "CANVA"],
        technical_skills=["Figma"],
        availability="WEEKDAY_EVENINGS",
        portfolio_url="https://www.behance.net/figma-designer",
    )
    project_id = create_project(client, required_technical_skills=["Figma"])

    response = client.get(f"/students/{student_id}/matches")

    assert response.status_code == 200
    projects = response.json()["projects"]
    assert len(projects) == 1
    assert projects[0]["project_id"] == project_id
    assert projects[0]["matched_skills"] == ["GRAPHIC_DESIGN", "CANVA"]
    assert projects[0]["matched_technical_skills"] == ["Figma"]
    assert projects[0]["score"] == 100
    assert projects[0]["priority_rank"] == 1


def test_match_recommendations_fall_back_to_rule_based_text_when_ai_is_unavailable(
    client: TestClient,
    monkeypatch,
) -> None:
    create_student(
        client,
        name="မေသဇင်",
        skills=["GRAPHIC_DESIGN", "CANVA"],
        availability="WEEKDAY_EVENINGS",
    )
    project_id = create_project(client)

    def ai_unavailable(*_args):
        raise projects.AIServiceNotConfiguredError("GEMINI_API_KEY is not configured.")

    monkeypatch.setattr(projects, "generate_match_recommendations", ai_unavailable)
    response = client.post(f"/projects/{project_id}/recommendations")

    assert response.status_code == 200
    recommendation = response.json()["recommendations"][0]
    assert recommendation["priority_rank"] == 1
    assert recommendation["score"] == 95
    assert recommendation["source"] == "RULE_BASED_FALLBACK"
    assert recommendation["recommendation"]
