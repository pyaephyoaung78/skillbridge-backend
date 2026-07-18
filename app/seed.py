"""Create repeatable demo users and student profiles for the SkillBridge MVP."""

from dataclasses import dataclass

from sqlmodel import Session, select

from app.database import create_db_and_tables, engine
from app.models.enums import UserRole, WorkPreference
from app.models.student_profile import StudentProfile
from app.models.user import User

DEMO_OWNER = {
    "name": "Tech Event Club",
    "role": UserRole.PROJECT_OWNER,
}

DEMO_STUDENTS = [
    {
        "name": "မေသဇင်",
        "university": "University of Yangon",
        "skills": ["GRAPHIC_DESIGN", "CANVA", "SOCIAL_MEDIA_DESIGN"],
        "availability": "WEEKDAY_EVENINGS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://www.behance.net/maythazin",
        "rating": 4.8,
        "completed_projects": 3,
    },
    {
        "name": "အိမ့်ပိုး",
        "university": "University of Yangon",
        "skills": ["GRAPHIC_DESIGN", "BRANDING"],
        "availability": "WEEKDAY_EVENINGS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://www.behance.net/eaintpo",
        "rating": 4.6,
        "completed_projects": 2,
    },
    {
        "name": "ကိုမင်း",
        "university": "Yangon Technological University",
        "skills": ["GRAPHIC_DESIGN", "ILLUSTRATION", "CANVA"],
        "availability": "WEEKENDS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://www.behance.net/komin",
        "rating": 4.5,
        "completed_projects": 2,
    },
    {
        "name": "စုစု",
        "university": "University of Yangon",
        "skills": ["CONTENT_WRITING", "TRANSLATION"],
        "availability": "WEEKDAY_EVENINGS",
        "work_preference": WorkPreference.BOTH,
        "portfolio_url": None,
        "rating": 4.4,
        "completed_projects": 2,
    },
    {
        "name": "သူရိန်",
        "university": "University of Computer Studies, Yangon",
        "skills": ["DIGITAL_MARKETING", "CONTENT_WRITING"],
        "availability": "WEEKDAY_DAYTIME",
        "work_preference": WorkPreference.ON_SITE,
        "portfolio_url": "https://www.linkedin.com/in/thurein-demo",
        "rating": 4.2,
        "completed_projects": 1,
    },
    {
        "name": "ဇင်မိုး",
        "university": "University of Computer Studies, Yangon",
        "skills": ["DATA_ANALYSIS", "PROGRAMMING"],
        "availability": "WEEKENDS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://github.com/zinmoe-demo",
        "rating": 4.7,
        "completed_projects": 3,
    },
    {
        "name": "နွယ်နွယ်",
        "university": "National Management Degree College",
        "skills": ["VIDEO_EDITING", "SOCIAL_MEDIA_DESIGN"],
        "availability": "WEEKDAY_EVENINGS",
        "work_preference": WorkPreference.BOTH,
        "portfolio_url": "https://www.behance.net/nwenwe",
        "rating": 4.3,
        "completed_projects": 1,
    },
    {
        "name": "ထက်အောင်",
        "university": "Yangon Technological University",
        "skills": ["PROGRAMMING", "DATA_ANALYSIS"],
        "availability": "WEEKENDS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://github.com/htetaung-demo",
        "rating": 4.9,
        "completed_projects": 4,
    },
    {
        "name": "သီရိ",
        "university": "University of Yangon",
        "skills": ["TRANSLATION", "CONTENT_WRITING"],
        "availability": "WEEKDAY_DAYTIME",
        "work_preference": WorkPreference.BOTH,
        "portfolio_url": None,
        "rating": 4.1,
        "completed_projects": 1,
    },
    {
        "name": "ကောင်းထက်",
        "university": "University of Computer Studies, Yangon",
        "skills": ["DIGITAL_MARKETING", "DATA_ANALYSIS"],
        "availability": "WEEKDAY_EVENINGS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://www.linkedin.com/in/kaunghtet-demo",
        "rating": 4.5,
        "completed_projects": 2,
    },
    {
        "name": "အေးအေး",
        "university": "National Management Degree College",
        "skills": ["CONTENT_WRITING", "SOCIAL_MEDIA_DESIGN"],
        "availability": "WEEKENDS",
        "work_preference": WorkPreference.ON_SITE,
        "portfolio_url": None,
        "rating": 4.0,
        "completed_projects": 1,
    },
    {
        "name": "လင်းထက်",
        "university": "Yangon Technological University",
        "skills": ["PROGRAMMING", "VIDEO_EDITING"],
        "availability": "WEEKDAY_EVENINGS",
        "work_preference": WorkPreference.BOTH,
        "portfolio_url": "https://github.com/linhtet-demo",
        "rating": 4.6,
        "completed_projects": 2,
    },
]


@dataclass(frozen=True)
class SeedSummary:
    created_users: int
    created_profiles: int


def find_user(session: Session, name: str, role: UserRole) -> User | None:
    return session.exec(
        select(User).where(User.name == name, User.role == role)
    ).first()


def seed_demo_data(session: Session) -> SeedSummary:
    """Insert missing demo records without duplicating records from a previous run."""
    created_users = 0
    created_profiles = 0

    owner = find_user(session, DEMO_OWNER["name"], DEMO_OWNER["role"])
    if owner is None:
        session.add(User(**DEMO_OWNER))
        created_users += 1

    for student_data in DEMO_STUDENTS:
        user = find_user(session, student_data["name"], UserRole.STUDENT)
        if user is None:
            user = User(name=student_data["name"], role=UserRole.STUDENT)
            session.add(user)
            session.flush()
            created_users += 1

        profile = session.exec(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        ).first()
        if profile is None:
            profile_data = {key: value for key, value in student_data.items() if key != "name"}
            session.add(StudentProfile(user_id=user.id, **profile_data))
            created_profiles += 1

    session.commit()
    return SeedSummary(
        created_users=created_users,
        created_profiles=created_profiles,
    )


def main() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        summary = seed_demo_data(session)

    print(
        "Seed complete: "
        f"{summary.created_users} user(s), "
        f"{summary.created_profiles} student profile(s) created."
    )


if __name__ == "__main__":
    main()
