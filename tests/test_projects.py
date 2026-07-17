from collections.abc import Generator
from datetime import date, timedelta

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


def create_user(client: TestClient, role: str) -> str:
    response = client.post("/users", json={"name": "Tech Event Club", "role": role})
    assert response.status_code == 201
    return response.json()["id"]


def project_payload(owner_id: str) -> dict[str, object]:
    return {
        "owner_id": owner_id,
        "title": "Tech Event Social Media Design",
        "description": "Create social-media posters for a university tech event.",
        "role": "GRAPHIC_DESIGNER",
        "required_skills": ["GRAPHIC_DESIGN", "CANVA"],
        "required_availability": "WEEKDAY_EVENINGS",
        "deadline": (date.today() + timedelta(days=7)).isoformat(),
        "work_type": "REMOTE",
        "budget_mmk": 60_000,
    }


def test_create_get_and_list_owner_projects(client: TestClient) -> None:
    owner_id = create_user(client, "PROJECT_OWNER")
    create_response = client.post("/projects", json=project_payload(owner_id))

    assert create_response.status_code == 201
    project = create_response.json()
    assert project["owner_name"] == "Tech Event Club"
    assert project["compensation_type"] == "PAID"
    assert project["status"] == "OPEN"

    get_response = client.get(f"/projects/{project['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["budget_mmk"] == 60_000

    list_response = client.get(f"/owners/{owner_id}/projects")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_project_rejects_invalid_budget_and_unknown_skills(client: TestClient) -> None:
    owner_id = create_user(client, "PROJECT_OWNER")
    invalid_budget = project_payload(owner_id)
    invalid_budget["budget_mmk"] = 0
    assert client.post("/projects", json=invalid_budget).status_code == 422

    invalid_skill = project_payload(owner_id)
    invalid_skill["required_skills"] = ["MADE_UP_SKILL"]
    assert client.post("/projects", json=invalid_skill).status_code == 422


def test_student_cannot_create_or_list_projects(client: TestClient) -> None:
    student_user_id = create_user(client, "STUDENT")

    create_response = client.post("/projects", json=project_payload(student_user_id))
    assert create_response.status_code == 422

    list_response = client.get(f"/owners/{student_user_id}/projects")
    assert list_response.status_code == 422
