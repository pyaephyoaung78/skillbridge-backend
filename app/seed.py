"""Create repeatable, realistic fictional demo data for the SkillBridge MVP."""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import Session, select

from app.database import create_db_and_tables, engine
from app.models.enums import UserRole, WorkPreference, WorkType
from app.models.project import Project
from app.models.student_profile import StudentProfile
from app.models.user import User

DEMO_OWNERS = [
    {"name": "Campus Tech Event Team", "role": UserRole.PROJECT_OWNER},
    {"name": "Mingalar Creative Studio", "role": UserRole.PROJECT_OWNER},
    {"name": "Thaton Startup Club", "role": UserRole.PROJECT_OWNER},
]

DEMO_STUDENTS = [
    {
        "name": "မေသဇင်",
        "university": "University of Yangon",
        "skills": ["GRAPHIC_DESIGN", "CANVA", "SOCIAL_MEDIA_DESIGN"],
        "technical_skills": ["Figma", "Canva", "Adobe Express"],
        "availability": "WEEKEND_EVENINGS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://www.behance.net/maythazin-demo",
        "rating": 4.8,
        "completed_projects": 3,
    },
    {
        "name": "အိမ့်ပိုး",
        "university": "University of Yangon",
        "skills": ["GRAPHIC_DESIGN", "BRANDING", "ILLUSTRATION"],
        "technical_skills": ["Figma", "Adobe Photoshop", "Illustrator"],
        "availability": "WEEKEND_EVENINGS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://www.behance.net/eaintpo-demo",
        "rating": 4.6,
        "completed_projects": 2,
    },
    {
        "name": "မင်းထက်",
        "university": "Yangon Technological University",
        "skills": ["GRAPHIC_DESIGN", "CANVA", "VIDEO_EDITING"],
        "technical_skills": ["Canva", "CapCut", "Adobe Premiere Pro"],
        "availability": "WEEKEND_MORNINGS",
        "work_preference": WorkPreference.BOTH,
        "portfolio_url": "https://www.behance.net/minhtet-demo",
        "rating": 4.5,
        "completed_projects": 2,
    },
    {
        "name": "အောင်မျိုးကျော်",
        "university": "Computer University (Thaton)",
        "skills": ["PROGRAMMING", "DATA_ANALYSIS"],
        "technical_skills": ["Python", "FastAPI", "SQL", "Git"],
        "availability": "WEEKEND_EVENINGS",
        "work_preference": WorkPreference.BOTH,
        "portfolio_url": "https://github.com/aungmyokyaw-demo",
        "rating": 4.7,
        "completed_projects": 3,
    },
    {
        "name": "ဇင်မိုး",
        "university": "University of Computer Studies, Yangon",
        "skills": ["DATA_ANALYSIS", "PROGRAMMING"],
        "technical_skills": ["Python", "Excel", "Power BI", "SQL"],
        "availability": "WEEKDAY_EVENINGS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://github.com/zinmoe-demo",
        "rating": 4.7,
        "completed_projects": 3,
    },
    {
        "name": "စုစု",
        "university": "University of Yangon",
        "skills": ["CONTENT_WRITING", "TRANSLATION", "SOCIAL_MEDIA_DESIGN"],
        "technical_skills": ["Copywriting", "Canva", "Google Docs"],
        "availability": "WEEKDAY_EVENINGS",
        "work_preference": WorkPreference.BOTH,
        "portfolio_url": "https://www.linkedin.com/in/susu-demo",
        "rating": 4.4,
        "completed_projects": 2,
    },
    {
        "name": "နွယ်နွယ်",
        "university": "National Management Degree College",
        "skills": ["VIDEO_EDITING", "SOCIAL_MEDIA_DESIGN"],
        "technical_skills": ["CapCut", "Adobe Premiere Pro", "Canva"],
        "availability": "WEEKEND_EVENINGS",
        "work_preference": WorkPreference.REMOTE,
        "portfolio_url": "https://www.behance.net/nwenwe-demo",
        "rating": 4.3,
        "completed_projects": 1,
    },
    {
        "name": "သီရိထက်",
        "university": "National Management Degree College",
        "skills": ["DIGITAL_MARKETING", "CONTENT_WRITING"],
        "technical_skills": ["Meta Ads", "Google Analytics", "Canva"],
        "availability": "WEEKEND_MORNINGS",
        "work_preference": WorkPreference.ON_SITE,
        "portfolio_url": "https://www.linkedin.com/in/thirihtet-demo",
        "rating": 4.2,
        "completed_projects": 1,
    },
]

DEMO_PROJECTS = [
    {
        "owner_name": "Campus Tech Event Team",
        "title": "Campus Tech Event Poster Designer",
        "description": "Design three event posters and social-media graphics for Campus Tech Event.",
        "role": "GRAPHIC_DESIGNER",
        "required_skills": ["GRAPHIC_DESIGN", "CANVA"],
        "required_technical_skills": ["Figma", "Canva"],
        "required_availability": "WEEKEND_EVENINGS",
        "deadline_days": 12,
        "work_type": WorkType.REMOTE,
        "budget_mmk": 60_000,
    },
    {
        "owner_name": "Campus Tech Event Team",
        "title": "Student Registration API Assistant",
        "description": "Build a small Python API for event registration and attendee data.",
        "role": "BACKEND_DEVELOPER",
        "required_skills": ["PROGRAMMING"],
        "required_technical_skills": ["Python", "FastAPI", "SQL"],
        "required_availability": "WEEKEND_EVENINGS",
        "deadline_days": 16,
        "work_type": WorkType.REMOTE,
        "budget_mmk": 120_000,
    },
    {
        "owner_name": "Mingalar Creative Studio",
        "title": "Weekend Social Media Content Creator",
        "description": "Prepare Burmese captions and simple Canva posts for a local business campaign.",
        "role": "CONTENT_CREATOR",
        "required_skills": ["CONTENT_WRITING", "SOCIAL_MEDIA_DESIGN"],
        "required_technical_skills": ["Copywriting", "Canva"],
        "required_availability": "WEEKDAY_EVENINGS",
        "deadline_days": 10,
        "work_type": WorkType.REMOTE,
        "budget_mmk": 45_000,
    },
    {
        "owner_name": "Mingalar Creative Studio",
        "title": "Short Product Promo Video Editor",
        "description": "Edit three short vertical product videos for Facebook and TikTok.",
        "role": "VIDEO_EDITOR",
        "required_skills": ["VIDEO_EDITING", "SOCIAL_MEDIA_DESIGN"],
        "required_technical_skills": ["CapCut", "Adobe Premiere Pro"],
        "required_availability": "WEEKEND_EVENINGS",
        "deadline_days": 14,
        "work_type": WorkType.REMOTE,
        "budget_mmk": 80_000,
    },
    {
        "owner_name": "Thaton Startup Club",
        "title": "Local Shop Sales Dashboard",
        "description": "Create a simple sales summary dashboard from spreadsheet data.",
        "role": "DATA_ANALYST",
        "required_skills": ["DATA_ANALYSIS"],
        "required_technical_skills": ["Excel", "Power BI"],
        "required_availability": "WEEKDAY_EVENINGS",
        "deadline_days": 18,
        "work_type": WorkType.REMOTE,
        "budget_mmk": 90_000,
    },
    {
        "owner_name": "Thaton Startup Club",
        "title": "Community Workshop Marketing Assistant",
        "description": "Support an on-site weekend workshop with Facebook promotion and content planning.",
        "role": "DIGITAL_MARKETING_ASSISTANT",
        "required_skills": ["DIGITAL_MARKETING", "CONTENT_WRITING"],
        "required_technical_skills": ["Meta Ads", "Google Analytics"],
        "required_availability": "WEEKEND_MORNINGS",
        "deadline_days": 20,
        "work_type": WorkType.ON_SITE,
        "budget_mmk": 70_000,
    },
]


@dataclass(frozen=True)
class SeedSummary:
    created_users: int
    created_profiles: int
    created_projects: int


def find_user(session: Session, name: str, role: UserRole) -> User | None:
    return session.exec(
        select(User).where(User.name == name, User.role == role)
    ).first()


def find_project(session: Session, owner_id, title: str) -> Project | None:
    return session.exec(
        select(Project).where(Project.owner_id == owner_id, Project.title == title)
    ).first()


def seed_demo_data(session: Session) -> SeedSummary:
    """Insert missing fictional demo records without duplicating a prior seed run."""
    created_users = 0
    created_profiles = 0
    created_projects = 0
    owners_by_name: dict[str, User] = {}

    for owner_data in DEMO_OWNERS:
        owner = find_user(session, owner_data["name"], owner_data["role"])
        if owner is None:
            owner = User(**owner_data)
            session.add(owner)
            session.flush()
            created_users += 1
        owners_by_name[owner_data["name"]] = owner

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
            session.add(StudentProfile(user_id=user.id, name=student_data["name"], **profile_data))
            created_profiles += 1

    for project_data in DEMO_PROJECTS:
        owner = owners_by_name[project_data["owner_name"]]
        if find_project(session, owner.id, project_data["title"]) is not None:
            continue
        project_fields = {
            key: value
            for key, value in project_data.items()
            if key not in {"owner_name", "deadline_days"}
        }
        session.add(
            Project(
                owner_id=owner.id,
                deadline=date.today() + timedelta(days=project_data["deadline_days"]),
                **project_fields,
            )
        )
        created_projects += 1

    session.commit()
    return SeedSummary(
        created_users=created_users,
        created_profiles=created_profiles,
        created_projects=created_projects,
    )


def main() -> None:
    create_db_and_tables()
    with Session(engine) as session:
        summary = seed_demo_data(session)

    print(
        "Seed complete: "
        f"{summary.created_users} user(s), "
        f"{summary.created_profiles} student profile(s), "
        f"{summary.created_projects} project(s) created."
    )


if __name__ == "__main__":
    main()
