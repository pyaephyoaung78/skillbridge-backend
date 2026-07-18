from sqlmodel import SQLModel, Session, create_engine, select

from app.models.enums import UserRole
from app.models.project import Project
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.seed import DEMO_OWNERS, DEMO_PROJECTS, DEMO_STUDENTS, seed_demo_data


def test_seed_creates_demo_data_once_without_duplicates(tmp_path) -> None:
    test_engine = create_engine(f"sqlite:///{tmp_path / 'skillbridge-seed-test.db'}")
    SQLModel.metadata.create_all(test_engine)

    with Session(test_engine) as session:
        first_run = seed_demo_data(session)
        second_run = seed_demo_data(session)

        users = session.exec(select(User)).all()
        profiles = session.exec(select(StudentProfile)).all()
        projects = session.exec(select(Project)).all()
        design_profiles = [
            profile
            for profile in profiles
            if "GRAPHIC_DESIGN" in profile.skills
        ]

    assert first_run.created_users == len(DEMO_STUDENTS) + len(DEMO_OWNERS)
    assert first_run.created_profiles == len(DEMO_STUDENTS)
    assert first_run.created_projects == len(DEMO_PROJECTS)
    assert second_run.created_users == 0
    assert second_run.created_profiles == 0
    assert second_run.created_projects == 0
    assert len(users) == len(DEMO_STUDENTS) + len(DEMO_OWNERS)
    assert len(profiles) == len(DEMO_STUDENTS)
    assert len(projects) == len(DEMO_PROJECTS)
    assert len(design_profiles) >= 3
    assert any(user.role == UserRole.PROJECT_OWNER for user in users)
