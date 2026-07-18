import json
import logging
import re
from datetime import date
from typing import Any

from pydantic import BaseModel, ValidationError

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

logger = logging.getLogger(__name__)


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
- `skills` must use only these SkillBridge matching categories: {", ".join(sorted(ALLOWED_SKILLS))}.
- `technical_skills` must preserve the exact technology, language, framework, tool, or software name spoken by the student in English.
- For example, Python, C++, C#, and Java must be returned in `technical_skills`; map them to `PROGRAMMING` in `skills`.
- Do not translate, transliterate, group, or replace exact technical terms in `technical_skills`.
- Return `availability` as one exact English code: WEEKDAY_MORNINGS, WEEKDAY_EVENINGS, WEEKEND_MORNINGS, WEEKEND_EVENINGS, or FLEXIBLE.
- Map Burmese availability phrases to those codes. For example, "စနေ၊ တနင်္ဂနွေ ညနေပိုင်း" means WEEKEND_EVENINGS.
- Return `work_preference` only as REMOTE, ON_SITE, or BOTH.
- Use an English university name when it is clear, for example "ကွန်ပျူတာတက္ကသိုလ် (သထုံ)" becomes "Computer University (Thaton)".
- Keep a person's name as spoken; do not translate or change it.
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
- `required_skills` contains only matching categories, such as GRAPHIC_DESIGN or PROGRAMMING.
- `required_technical_skills` preserves exact English tools, software, languages, or frameworks, such as Figma, Canva, Python, C++, or Java. Do not translate or replace these terms.
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
            f"matched_technical_skills: {', '.join(candidate.matched_technical_skills)}; "
            f"availability: {candidate.availability}; "
            f"project_required_availability: {project.required_availability}; "
            f"work_preference: {candidate.work_preference}; "
            f"portfolio: {'yes' if candidate.portfolio_url else 'no'}"
        )
        for candidate in candidates
    )
    return f"""
Write one short, friendly Burmese recommendation for each SkillBridge priority candidate.

Project: {project.title or 'Untitled project'}
Project work type: {project.work_type}
Required skills: {', '.join(project.required_skills)}
Required technical skills: {', '.join(project.required_technical_skills or [])}

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


def _gemini_json(prompt: str, response_schema: type[BaseModel]) -> str:
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
                "base_url": "https://gemini-proxy35.aungmkyaw03.workers.dev"
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
    # Keep this server-side only. It is essential for diagnosing schema drift,
    # but raw AI output must never be returned to the mobile client.
    logger.info("Gemini raw %s response: %s", response_schema.__name__, response.text)
    return response.text


def _strip_json_code_fence(raw_json: str) -> str:
    """Accept Gemini JSON even if a proxy/model wraps it in a Markdown fence."""
    cleaned_json = raw_json.strip()
    cleaned_json = re.sub(r"^```(?:json)?\s*", "", cleaned_json, flags=re.IGNORECASE)
    cleaned_json = re.sub(r"\s*```$", "", cleaned_json)
    return cleaned_json.strip()


def _load_gemini_object(raw_json: str, schema_name: str) -> dict[str, Any]:
    try:
        parsed_json = json.loads(_strip_json_code_fence(raw_json))
    except json.JSONDecodeError as error:
        logger.warning("Gemini %s response was not valid JSON: %s", schema_name, error)
        return {}
    if not isinstance(parsed_json, dict):
        logger.warning("Gemini %s response must be a JSON object.", schema_name)
        return {}
    return parsed_json


def _optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned_value = value.strip()
    return cleaned_value or None


def _text_list(value: Any) -> list[str]:
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list):
        return []
    cleaned_values = [_optional_text(item) for item in values]
    return [item for item in cleaned_values if item is not None]


def _unique_case_insensitive(values: list[str]) -> list[str]:
    unique_values: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        normalized_value = value.casefold()
        if normalized_value not in seen_values:
            unique_values.append(value)
            seen_values.add(normalized_value)
    return unique_values


_SKILL_ALIASES = {
    **{skill.casefold(): skill for skill in ALLOWED_SKILLS},
    "graphic design": "GRAPHIC_DESIGN",
    "graphic designer": "GRAPHIC_DESIGN",
    "social media": "SOCIAL_MEDIA_DESIGN",
    "social media design": "SOCIAL_MEDIA_DESIGN",
    "content writing": "CONTENT_WRITING",
    "digital marketing": "DIGITAL_MARKETING",
    "data analysis": "DATA_ANALYSIS",
    "video editing": "VIDEO_EDITING",
}


def _normalize_matching_skills(value: Any) -> list[str]:
    normalized_skills: list[str] = []
    for raw_skill in _text_list(value):
        normalized_key = raw_skill.casefold().replace("_", " ").replace("-", " ")
        normalized_key = re.sub(r"\s+", " ", normalized_key).strip()
        skill = _SKILL_ALIASES.get(normalized_key)
        if skill is not None and skill not in normalized_skills:
            normalized_skills.append(skill)
    return normalized_skills


def _normalize_work_preference(value: Any) -> str | None:
    raw_value = _optional_text(value)
    if raw_value is None:
        return None
    normalized_value = re.sub(r"[\s_-]+", "", raw_value.casefold())
    if normalized_value in {"remote", "remotework"} or "အဝေး" in raw_value:
        return "REMOTE"
    if normalized_value in {"onsite", "onsitework"} or "ရုံး" in raw_value:
        return "ON_SITE"
    if normalized_value in {"both", "any"} or "နှစ်မျိုး" in raw_value:
        return "BOTH"
    return None


def _normalize_availability(value: Any) -> str | None:
    raw_value = _optional_text(value)
    if raw_value is None:
        return None
    uppercase_value = raw_value.upper()
    valid_codes = {
        "WEEKDAY_MORNINGS",
        "WEEKDAY_EVENINGS",
        "WEEKEND_MORNINGS",
        "WEEKEND_EVENINGS",
        "FLEXIBLE",
    }
    if uppercase_value in valid_codes:
        return uppercase_value

    normalized_value = raw_value.casefold()
    if "flexible" in normalized_value or "အချိန်မရွေး" in raw_value:
        return "FLEXIBLE"
    is_weekend = any(word in raw_value for word in ("စနေ", "တနင်္ဂနွေ")) or "weekend" in normalized_value
    is_weekday = any(
        word in raw_value
        for word in ("တနင်္လာ", "အင်္ဂါ", "ဗုဒ္ဓဟူး", "ကြာသပတေး", "သောကြာ")
    ) or "weekday" in normalized_value
    is_morning = "မနက်" in raw_value or "morning" in normalized_value
    is_evening = any(word in raw_value for word in ("ညနေ", "ညပိုင်း")) or "evening" in normalized_value

    if is_weekend and is_morning:
        return "WEEKEND_MORNINGS"
    if is_weekend and is_evening:
        return "WEEKEND_EVENINGS"
    if is_weekday and is_morning:
        return "WEEKDAY_MORNINGS"
    if is_weekday and is_evening:
        return "WEEKDAY_EVENINGS"
    return None


def _missing_field_names(value: Any) -> set[str]:
    return set(_text_list(value))


def _student_draft_from_raw_json(raw_json: str) -> StudentProfileDraft:
    payload = _load_gemini_object(raw_json, "StudentProfileDraft")
    missing_fields = _missing_field_names(payload.get("missing_fields"))
    skills = _normalize_matching_skills(payload.get("skills"))
    technical_skills = _unique_case_insensitive(_text_list(payload.get("technical_skills")))
    availability = _normalize_availability(payload.get("availability"))
    work_preference = _normalize_work_preference(payload.get("work_preference"))

    if not skills:
        missing_fields.add("skills")
    if availability is None:
        missing_fields.add("availability")
    if work_preference is None:
        missing_fields.add("work_preference")

    return StudentProfileDraft(
        name=_optional_text(payload.get("name")),
        university=_optional_text(payload.get("university")),
        skills=skills,
        technical_skills=technical_skills,
        availability=availability,
        work_preference=work_preference,
        missing_fields=sorted(missing_fields),
    )


def _normalize_work_type(value: Any) -> str | None:
    preference = _normalize_work_preference(value)
    return preference if preference in {"REMOTE", "ON_SITE"} else None


def _normalize_deadline(value: Any) -> date | None:
    raw_value = _optional_text(value)
    if raw_value is None:
        return None
    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        return None


def _normalize_budget(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        budget = int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None
    return budget if budget > 0 else None


def _project_draft_from_raw_json(raw_json: str) -> ProjectDraft:
    payload = _load_gemini_object(raw_json, "ProjectDraft")
    missing_fields = _missing_field_names(payload.get("missing_fields"))
    required_skills = _normalize_matching_skills(payload.get("required_skills"))
    required_technical_skills = _unique_case_insensitive(
        _text_list(payload.get("required_technical_skills"))
    )
    required_availability = _normalize_availability(payload.get("required_availability"))
    deadline = _normalize_deadline(payload.get("deadline"))
    work_type = _normalize_work_type(payload.get("work_type"))
    budget_mmk = _normalize_budget(payload.get("budget_mmk"))
    fields_to_check = {
        "description": _optional_text(payload.get("description")),
        "role": _optional_text(payload.get("role")),
        "required_skills": required_skills,
        "required_availability": required_availability,
        "deadline": deadline,
        "work_type": work_type,
        "budget_mmk": budget_mmk,
    }
    missing_fields.update(field for field, value in fields_to_check.items() if not value)

    return ProjectDraft(
        title=_optional_text(payload.get("title")),
        description=fields_to_check["description"],
        role=fields_to_check["role"],
        required_skills=required_skills,
        required_technical_skills=required_technical_skills,
        required_availability=required_availability,
        deadline=deadline,
        work_type=work_type,
        budget_mmk=budget_mmk,
        missing_fields=sorted(missing_fields),
    )


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
        draft = _student_draft_from_raw_json(
            _gemini_json(_student_prompt(text), StudentProfileDraft)
        )
    except ValidationError:
        logger.exception("Gemini student draft could not be normalized")
        draft = StudentProfileDraft(
            missing_fields=["name", "university", "skills", "availability", "work_preference"]
        )
    return _normalize_student_missing_fields(draft)


def parse_project_brief(text: str) -> ProjectDraft:
    """Use Gemini only to draft project fields; the owner still confirms before save."""
    try:
        draft = _project_draft_from_raw_json(
            _gemini_json(_project_prompt(text), ProjectDraft)
        )
    except ValidationError:
        logger.exception("Gemini project draft could not be normalized")
        draft = ProjectDraft(
            missing_fields=[
                "description",
                "role",
                "required_skills",
                "required_availability",
                "deadline",
                "work_type",
                "budget_mmk",
            ]
        )
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
