from datetime import date

from pydantic import ValidationError

from app.config import get_settings
from app.constants import ALLOWED_SKILLS
from app.models.project import Project
from app.schemas.ai import (
    MatchRecommendationDraft,
    MatchRecommendationsDraft,
    ProjectDraft,
    StudentProfileDraft,
)
from app.schemas.match import MatchCandidateRead


class AIServiceNotConfiguredError(Exception):
    """Raised when a required external AI credential or setting is absent."""


class AIServiceError(Exception):
    """Raised when an external AI provider cannot create a usable response."""


def _student_prompt(text: str) -> str:
    return f"""
Extract a SkillBridge student profile from the confirmed Burmese or English text below.

Text:
{text}

Rules:
- Return structured JSON only through the response schema.
- Never invent a name, university, skill, availability, or work preference.
- For unknown fields, return null (or an empty skills list) and add the API field name to missing_fields.
- Allowed skills only: {", ".join(sorted(ALLOWED_SKILLS))}.
- work_preference must be REMOTE, ON_SITE, or BOTH.
- A portfolio URL is entered manually elsewhere; do not extract one.
""".strip()


def _project_prompt(text: str) -> str:
    today = date.today().isoformat()
    return f"""
Extract a SkillBridge paid-project draft from the confirmed Burmese or English text below.

Today is {today}.

Text:
{text}

Rules:
- Return structured JSON only through the response schema.
- Never invent title, description, role, skills, availability, deadline, work type, or budget.
- For unknown fields, return null (or an empty required_skills list) and add the API field name to missing_fields.
- Convert a clear relative deadline such as Friday into ISO date YYYY-MM-DD using today's date only when unambiguous.
- Allowed required_skills only: {", ".join(sorted(ALLOWED_SKILLS))}.
- work_type must be REMOTE or ON_SITE.
- budget_mmk must be a positive integer in MMK. Do not create a budget if it was not stated.
- This MVP always represents paid work, so do not return compensation type or project status.
""".strip()


def _match_recommendation_prompt(
    project: Project,
    candidates: list[MatchCandidateRead],
) -> str:
    candidate_lines = "\n".join(
        (
            f"- student_id: {candidate.student_id}; name: {candidate.name}; "
            f"rank: {candidate.priority_rank}; score: {candidate.score}%; "
            f"matched_skills: {', '.join(candidate.matched_skills)}; "
            f"availability: {candidate.availability}; "
            f"project_required_availability: {project.required_availability}; "
            f"work_preference: {candidate.work_preference}; "
            f"portfolio: {'yes' if candidate.portfolio_url else 'no'}"
        )
        for candidate in candidates
    )
    return f"""
Write one short, friendly Burmese recommendation for each SkillBridge priority candidate.

Project: {project.title}
Project work type: {project.work_type}
Required skills: {', '.join(project.required_skills)}

Candidates:
{candidate_lines}

Rules:
- Return structured JSON only through the response schema.
- Return exactly one item for each supplied student_id.
- Keep the exact student_id values.
- Explain the score using only the supplied facts: matching skills, availability, work preference, and portfolio.
- Mention the score percentage naturally.
- Do not invent experience, ratings, availability, or skills.
- Write each recommendation in one or two short Burmese sentences.
""".strip()


def _gemini_json(prompt: str, response_schema: type[StudentProfileDraft] | type[ProjectDraft]) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise AIServiceNotConfiguredError("GEMINI_API_KEY is not configured.")

    try:
        from google import genai
        from google.genai import types

        # Initialize the client with your Cloudflare Worker proxy endpoint
        client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={
                "api_endpoint": "gemini-proxy35.aungmkyaw03.workers.dev"
            }
        )
        
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
    except Exception as error:
        raise AIServiceError("Gemini could not create a draft.") from error

    if not response.text:
        raise AIServiceError("Gemini returned an empty draft.")
    return response.text


def _normalize_student_missing_fields(draft: StudentProfileDraft) -> StudentProfileDraft:
    required_fields = {
        "name": draft.name,
        "university": draft.university,
        "skills": draft.skills,
        "availability": draft.availability,
        "work_preference": draft.work_preference,
    }
    missing = set(draft.missing_fields)
    missing.update(field for field, value in required_fields.items() if not value)
    return draft.model_copy(update={"missing_fields": sorted(missing)})


def _normalize_project_missing_fields(draft: ProjectDraft) -> ProjectDraft:
    required_fields = {
        "title": draft.title,
        "description": draft.description,
        "role": draft.role,
        "required_skills": draft.required_skills,
        "required_availability": draft.required_availability,
        "deadline": draft.deadline,
        "work_type": draft.work_type,
        "budget_mmk": draft.budget_mmk,
    }
    missing = set(draft.missing_fields)
    missing.update(field for field, value in required_fields.items() if not value)
    return draft.model_copy(update={"missing_fields": sorted(missing)})


def parse_student_profile(text: str) -> StudentProfileDraft:
    """Use Gemini only to draft fields; the user still confirms before save."""
    try:
        draft = StudentProfileDraft.model_validate_json(
            _gemini_json(_student_prompt(text), StudentProfileDraft)
        )
    except ValidationError as error:
        raise AIServiceError("Gemini returned an invalid student profile draft.") from error
    return _normalize_student_missing_fields(draft)


def parse_project_brief(text: str) -> ProjectDraft:
    """Use Gemini only to draft project fields; the owner still confirms before save."""
    try:
        draft = ProjectDraft.model_validate_json(
            _gemini_json(_project_prompt(text), ProjectDraft)
        )
    except ValidationError as error:
        raise AIServiceError("Gemini returned an invalid project draft.") from error
    return _normalize_project_missing_fields(draft)


def generate_match_recommendations(
    project: Project,
    candidates: list[MatchCandidateRead],
) -> list[MatchRecommendationDraft]:
    """Generate factual Burmese explanations for the already-ranked top candidates."""
    try:
        draft = MatchRecommendationsDraft.model_validate_json(
            _gemini_json(
                _match_recommendation_prompt(project, candidates),
                MatchRecommendationsDraft,
            )
        )
    except ValidationError as error:
        raise AIServiceError("Gemini returned invalid match recommendations.") from error
    return draft.recommendations
