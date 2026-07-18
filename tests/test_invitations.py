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


def create_user(client: TestClient, name: str, role: str) -> str:
    response = client.post("/users", json={"name": name, "role": role})
    assert response.status_code == 201
    return response.json()["id"]


def create_student(client: TestClient, name: str) -> tuple[str, str]:
    user_id = create_user(client, name, "STUDENT")
    response = client.post(
        "/students",
        json={
            "user_id": user_id,
            "name": name,
            "university": "University of Yangon",
            "skills": ["GRAPHIC_DESIGN", "CANVA"],
            "availability": "WEEKDAY_EVENINGS",
            "work_preference": "REMOTE",
            "portfolio_url": "https://www.behance.net/example",
            "is_available": True,
        },
    )
    assert response.status_code == 201
    return user_id, response.json()["id"]


def create_project(client: TestClient) -> tuple[str, str]:
    owner_id = create_user(client, "Tech Event Club", "PROJECT_OWNER")
    response = client.post(
        "/projects",
        json={
            "owner_id": owner_id,
            "title": "Tech Event Social Media Design",
            "description": "Create social-media posters for a university tech event.",
            "role": "GRAPHIC_DESIGNER",
            "required_skills": ["GRAPHIC_DESIGN", "CANVA"],
            "required_availability": "WEEKDAY_EVENINGS",
            "deadline": (date.today() + timedelta(days=7)).isoformat(),
            "work_type": "REMOTE",
            "budget_mmk": 60_000,
        },
    )
    assert response.status_code == 201
    return owner_id, response.json()["id"]


def invitation_payload(owner_id: str, project_id: str, student_id: str) -> dict[str, str]:
    return {
        "owner_id": owner_id,
        "project_id": project_id,
        "student_id": student_id,
    }


def test_accepting_invitation_fills_project_and_prevents_more_invitations(
    client: TestClient,
) -> None:
    owner_id, project_id = create_project(client)
    _, first_student_id = create_student(client, "မေသဇင်")
    _, second_student_id = create_student(client, "ကိုမင်း")

    create_response = client.post(
        "/invitations",
        json=invitation_payload(owner_id, project_id, first_student_id),
    )
    assert create_response.status_code == 201
    invitation = create_response.json()
    assert invitation["status"] == "PENDING"
    assert invitation["budget_mmk"] == 60_000

    inbox_response = client.get(f"/students/{first_student_id}/invitations")
    assert inbox_response.status_code == 200
    assert len(inbox_response.json()) == 1

    second_invite_response = client.post(
        "/invitations",
        json=invitation_payload(owner_id, project_id, second_student_id),
    )
    assert second_invite_response.status_code == 409

    accept_response = client.post(
        f"/invitations/{invitation['id']}/accept",
        json={"student_id": first_student_id},
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["status"] == "ACCEPTED"
    assert accept_response.json()["project_status"] == "FILLED"

    project_response = client.get(f"/projects/{project_id}")
    assert project_response.json()["status"] == "FILLED"

    later_invite_response = client.post(
        "/invitations",
        json=invitation_payload(owner_id, project_id, second_student_id),
    )
    assert later_invite_response.status_code == 409


def test_declining_keeps_project_open_for_another_eligible_student(client: TestClient) -> None:
    owner_id, project_id = create_project(client)
    _, first_student_id = create_student(client, "မေသဇင်")
    _, second_student_id = create_student(client, "ကိုမင်း")

    first_invitation = client.post(
        "/invitations",
        json=invitation_payload(owner_id, project_id, first_student_id),
    ).json()
    decline_response = client.post(
        f"/invitations/{first_invitation['id']}/decline",
        json={"student_id": first_student_id},
    )
    assert decline_response.status_code == 200
    assert decline_response.json()["status"] == "DECLINED"
    assert decline_response.json()["project_status"] == "OPEN"

    second_invitation = client.post(
        "/invitations",
        json=invitation_payload(owner_id, project_id, second_student_id),
    )
    assert second_invitation.status_code == 201
    assert second_invitation.json()["status"] == "PENDING"


def test_only_project_owner_and_invited_student_can_take_invitation_actions(
    client: TestClient,
) -> None:
    owner_id, project_id = create_project(client)
    _, student_id = create_student(client, "မေသဇင်")
    other_student_user_id, other_student_id = create_student(client, "ကိုမင်း")

    invitation = client.post(
        "/invitations",
        json=invitation_payload(owner_id, project_id, student_id),
    ).json()
    wrong_student_response = client.post(
        f"/invitations/{invitation['id']}/accept",
        json={"student_id": other_student_id},
    )
    assert wrong_student_response.status_code == 403

    wrong_owner_response = client.post(
        "/invitations",
        json=invitation_payload(other_student_user_id, project_id, other_student_id),
    )
    assert wrong_owner_response.status_code == 403
