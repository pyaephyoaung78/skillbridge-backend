from app.models.enums import WorkPreference, WorkType
from app.models.project import Project
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.match import MatchCandidateRead

SKILL_POINTS = 55
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


def student_is_eligible_for_project(student: StudentProfile, project: Project) -> bool:
    """Apply the matching hard filters before an owner can send an invitation."""
    return (
        student.is_available
        and bool(matched_skills(student, project))
        and work_preference_matches(student, project)
    )


def calculate_score(student: StudentProfile, project: Project) -> tuple[int, list[str]]:
    """Calculate the documented, transparent 100-point match score."""
    matching_skills = matched_skills(student, project)
    skill_score = round(SKILL_POINTS * len(matching_skills) / len(project.required_skills))
    availability_score = (
        AVAILABILITY_POINTS
        if student.availability == project.required_availability
        else 0
    )
    work_type_score = WORK_TYPE_POINTS
    portfolio_score = PORTFOLIO_POINTS if student.portfolio_url else 0

    return skill_score + availability_score + work_type_score + portfolio_score, matching_skills


def recommendation_explanation(
    student: StudentProfile,
    project: Project,
    matching_skills: list[str],
) -> str:
    """Create a clear explanation from rules, without unexplained AI guesses."""
    skill_text = ", ".join(matching_skills)
    availability_text = (
        "လိုအပ်သော အချိန်နှင့်ကိုက်ညီပြီး"
        if student.availability == project.required_availability
        else "available ဖြစ်ပြီး"
    )
    work_text = "remote work" if project.work_type == WorkType.REMOTE else "on-site work"

    return (
        f"{skill_text} skills များကိုက်ညီပြီး "
        f"{availability_text} {work_text} ကို လက်ခံထားပါသည်။"
    )


def find_top_matches(
    project: Project,
    students_with_users: list[tuple[StudentProfile, User]],
    limit: int = 3,
) -> list[MatchCandidateRead]:
    """Filter eligible students, score them, and return only the best candidates."""
    candidates: list[MatchCandidateRead] = []

    for student, user in students_with_users:
        if not student_is_eligible_for_project(student, project):
            continue

        matching_skills = matched_skills(student, project)
        score, matching_skills = calculate_score(student, project)
        candidates.append(
            MatchCandidateRead(
                student_id=student.id,
                name=user.name,
                skills=student.skills,
                availability=student.availability,
                work_preference=student.work_preference,
                portfolio_url=student.portfolio_url,
                rating=student.rating,
                completed_projects=student.completed_projects,
                matched_skills=matching_skills,
                score=score,
                explanation=recommendation_explanation(
                    student,
                    project,
                    matching_skills,
                ),
            )
        )

    return sorted(candidates, key=lambda candidate: (-candidate.score, candidate.name))[:limit]
