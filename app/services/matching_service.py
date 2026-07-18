from app.models.enums import ProjectStatus, WorkPreference, WorkType
from app.models.project import Project
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.match import MatchCandidateRead, ProjectMatchRead

CATEGORY_SKILL_POINTS = 45
TECHNICAL_SKILL_POINTS = 10
SKILL_POINTS_WITHOUT_TECHNICAL_REQUIREMENTS = 55
AVAILABILITY_POINTS = 25
WORK_TYPE_POINTS = 15
PORTFOLIO_POINTS = 5


def work_preference_matches(student: StudentProfile, project: Project) -> bool:
    """Return whether the student accepts the project's remote/on-site type."""
    return student.work_preference in {
        WorkPreference.BOTH,
        WorkPreference(project.work_type.value),
    }


def matched_skills(student: StudentProfile, project: Project) -> list[str]:
    """Keep the project's skill order so the result is stable for the UI."""
    student_skills = set(student.skills)
    return [skill for skill in project.required_skills if skill in student_skills]


def matched_technical_skills(student: StudentProfile, project: Project) -> list[str]:
    """Match technical terms case-insensitively while keeping the project's display text."""
    student_technical_skills = {
        skill.casefold() for skill in (student.technical_skills or [])
    }
    return [
        skill
        for skill in (project.required_technical_skills or [])
        if skill.casefold() in student_technical_skills
    ]


def student_is_eligible_for_project(student: StudentProfile, project: Project) -> bool:
    """Apply the matching hard filters before an owner can send an invitation."""
    return (
        student.is_available
        and bool(matched_skills(student, project))
        and (
            not project.required_technical_skills
            or bool(matched_technical_skills(student, project))
        )
        and work_preference_matches(student, project)
    )


def calculate_score(
    student: StudentProfile,
    project: Project,
) -> tuple[int, list[str], list[str]]:
    """Calculate the documented, transparent 100-point match score."""
    matching_skills = matched_skills(student, project)
    matching_technical_skills = matched_technical_skills(student, project)
    if project.required_technical_skills:
        category_skill_score = round(
            CATEGORY_SKILL_POINTS * len(matching_skills) / len(project.required_skills)
        )
        technical_skill_score = round(
            TECHNICAL_SKILL_POINTS
            * len(matching_technical_skills)
            / len(project.required_technical_skills)
        )
        skill_score = category_skill_score + technical_skill_score
    else:
        skill_score = round(
            SKILL_POINTS_WITHOUT_TECHNICAL_REQUIREMENTS
            * len(matching_skills)
            / len(project.required_skills)
        )
    availability_score = (
        AVAILABILITY_POINTS
        if student.availability == project.required_availability
        else 0
    )
    work_type_score = WORK_TYPE_POINTS
    portfolio_score = PORTFOLIO_POINTS if student.portfolio_url else 0

    return (
        skill_score + availability_score + work_type_score + portfolio_score,
        matching_skills,
        matching_technical_skills,
    )


def recommendation_explanation(
    student: StudentProfile,
    project: Project,
    matching_skills: list[str],
    matching_technical_skills: list[str],
) -> str:
    """Create a clear explanation from rules, without unexplained AI guesses."""
    skill_text = ", ".join(matching_skills)
    availability_text = (
        "လိုအပ်သော အချိန်နှင့်ကိုက်ညီပြီး"
        if student.availability == project.required_availability
        else "available ဖြစ်ပြီး"
    )
    work_text = "remote work" if project.work_type == WorkType.REMOTE else "on-site work"
    technical_text = (
        f" {', '.join(matching_technical_skills)} technical skills များလည်းကိုက်ညီပြီး"
        if matching_technical_skills
        else ""
    )

    return (
        f"{skill_text} skills များကိုက်ညီပြီး{technical_text} "
        f"{availability_text} {work_text} ကို လက်ခံထားပါသည်။"
    )


def find_ranked_matches(
    project: Project,
    students_with_users: list[tuple[StudentProfile, User]],
) -> list[MatchCandidateRead]:
    """Filter eligible students and return every match in transparent score order."""
    candidates: list[MatchCandidateRead] = []

    for student, user in students_with_users:
        if not student_is_eligible_for_project(student, project):
            continue

        score, matching_skills, matching_technical_skills = calculate_score(student, project)
        candidates.append(
            MatchCandidateRead(
                student_id=student.id,
                name=student.name or "Unnamed student",
                skills=student.skills,
                technical_skills=student.technical_skills or [],
                availability=student.availability,
                work_preference=student.work_preference,
                portfolio_url=student.portfolio_url,
                rating=student.rating,
                completed_projects=student.completed_projects,
                matched_skills=matching_skills,
                matched_technical_skills=matching_technical_skills,
                score=score,
                explanation=recommendation_explanation(
                    student,
                    project,
                    matching_skills,
                    matching_technical_skills,
                ),
            )
        )

    ranked_candidates = sorted(candidates, key=lambda candidate: (-candidate.score, candidate.name))
    return [
        candidate.model_copy(update={"priority_rank": index if index <= 3 else None})
        for index, candidate in enumerate(ranked_candidates, start=1)
    ]


def project_match_explanation(
    student: StudentProfile,
    project: Project,
    matching_skills: list[str],
    matching_technical_skills: list[str],
) -> str:
    """Explain a project recommendation using the same transparent matching facts."""
    technical_text = (
        f" {', '.join(matching_technical_skills)} technical skills များလည်းကိုက်ညီပြီး"
        if matching_technical_skills
        else ""
    )
    availability_text = (
        "လိုအပ်သော အချိန်နှင့်ကိုက်ညီပါသည်"
        if student.availability == project.required_availability
        else "available ဖြစ်ပါသည်"
    )
    return (
        f"{', '.join(matching_skills)} skills များကိုက်ညီပြီး{technical_text} "
        f"{availability_text}။"
    )


def find_ranked_project_matches(
    student: StudentProfile,
    projects_with_owners: list[tuple[Project, User]],
) -> list[ProjectMatchRead]:
    """Return OPEN projects that are eligible for this student, ranked by the shared score."""
    project_matches: list[ProjectMatchRead] = []

    for project, owner in projects_with_owners:
        if project.status != ProjectStatus.OPEN or not student_is_eligible_for_project(student, project):
            continue

        score, matching_skills, matching_technical_skills = calculate_score(student, project)
        project_matches.append(
            ProjectMatchRead(
                project_id=project.id,
                owner_id=owner.id,
                owner_name=owner.name,
                title=project.title,
                description=project.description,
                role=project.role,
                required_skills=project.required_skills,
                required_technical_skills=project.required_technical_skills or [],
                required_availability=project.required_availability,
                deadline=project.deadline,
                work_type=project.work_type,
                budget_mmk=project.budget_mmk,
                matched_skills=matching_skills,
                matched_technical_skills=matching_technical_skills,
                score=score,
                explanation=project_match_explanation(
                    student,
                    project,
                    matching_skills,
                    matching_technical_skills,
                ),
            )
        )

    ranked_projects = sorted(
        project_matches,
        key=lambda project: (-project.score, project.deadline, project.title or ""),
    )
    return [
        project.model_copy(update={"priority_rank": index if index <= 3 else None})
        for index, project in enumerate(ranked_projects, start=1)
    ]
