from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from app.database import get_session
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


def create_user(client: TestClient, role: str = "STUDENT") -> str:
    response = client.post("/users", json={"name": "မေသဇင်", "role": role})
    assert response.status_code == 201
    return response.json()["id"]


def test_create_get_and_update_student_profile(client: TestClient) -> None:
    user_id = create_user(client)
    create_response = client.post(
        "/students",
        json={
            "user_id": user_id,
            "university": "University of Yangon",
            "skills": ["GRAPHIC_DESIGN", "CANVA"],
            "availability": "WEEKDAY_EVENINGS",
            "work_preference": "REMOTE",
            "portfolio_url": "https://www.behance.net/example",
        },
    )

    assert create_response.status_code == 201
    student = create_response.json()
    assert student["name"] == "မေသဇင်"
    assert student["is_available"] is True

    get_response = client.get(f"/students/{student['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["skills"] == ["GRAPHIC_DESIGN", "CANVA"]

    update_response = client.patch(
        f"/students/{student['id']}",
        json={"is_available": False, "availability": "WEEKENDS"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_available"] is False
    assert update_response.json()["availability"] == "WEEKENDS"


def test_student_profile_rejects_unknown_skills_and_duplicate_profiles(
    client: TestClient,
) -> None:
    user_id = create_user(client)
    invalid_response = client.post(
        "/students",
        json={
            "user_id": user_id,
            "university": "University of Yangon",
            "skills": ["MADE_UP_SKILL"],
            "availability": "WEEKDAY_EVENINGS",
            "work_preference": "REMOTE",
        },
    )
    assert invalid_response.status_code == 422

    valid_payload = {
        "user_id": user_id,
        "university": "University of Yangon",
        "skills": ["GRAPHIC_DESIGN"],
        "availability": "WEEKDAY_EVENINGS",
        "work_preference": "REMOTE",
    }
    assert client.post("/students", json=valid_payload).status_code == 201

    duplicate_response = client.post("/students", json=valid_payload)
    assert duplicate_response.status_code == 409


def test_project_owner_cannot_create_student_profile(client: TestClient) -> None:
    owner_id = create_user(client, role="PROJECT_OWNER")

    response = client.post(
        "/students",
        json={
            "user_id": owner_id,
            "university": "University of Yangon",
            "skills": ["GRAPHIC_DESIGN"],
            "availability": "WEEKDAY_EVENINGS",
            "work_preference": "REMOTE",
        },
    )

    assert response.status_code == 422
