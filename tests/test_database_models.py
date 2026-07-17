from sqlalchemy import inspect

from app.database import create_db_and_tables, engine
from app.models.enums import ProjectStatus, UserRole, WorkPreference, WorkType
from app.models.project import Project
from app.models.student_profile import StudentProfile
from app.models.user import User


def test_database_tables_are_created() -> None:
    create_db_and_tables()

    table_names = set(inspect(engine).get_table_names())

    assert {"users", "student_profiles", "projects", "invitations"} <= table_names


def test_models_have_expected_defaults() -> None:
    user = User(name="မေသဇင်", role=UserRole.STUDENT)
    student = StudentProfile(
        user_id=user.id,
        university="University of Yangon",
        skills=["GRAPHIC_DESIGN", "CANVA"],
        availability="WEEKDAY_EVENINGS",
        work_preference=WorkPreference.REMOTE,
    )
    project = Project(
        owner_id=user.id,
        title="Tech Event Social Media Design",
        description="Create social-media posters.",
        role="GRAPHIC_DESIGNER",
        required_skills=["GRAPHIC_DESIGN", "CANVA"],
        required_availability="WEEKDAY_EVENINGS",
        deadline="2026-07-24",
        work_type=WorkType.REMOTE,
        budget_mmk=60_000,
    )

    assert student.is_available is True
    assert project.compensation_type == "PAID"
    assert project.status is ProjectStatus.OPEN
