ALLOWED_SKILLS = {
    "GRAPHIC_DESIGN",
    "CANVA",
    "SOCIAL_MEDIA_DESIGN",
    "BRANDING",
    "ILLUSTRATION",
    "CONTENT_WRITING",
    "DIGITAL_MARKETING",
    "DATA_ANALYSIS",
    "VIDEO_EDITING",
    "PROGRAMMING",
    "TRANSLATION",
}


def validate_skills(skills: list[str]) -> list[str]:
    """Reject an empty list or skills outside the shared SkillBridge catalog."""
    if not skills:
        raise ValueError("At least one skill is required.")

    unknown_skills = set(skills) - ALLOWED_SKILLS
    if unknown_skills:
        names = ", ".join(sorted(unknown_skills))
        raise ValueError(f"Unsupported skill(s): {names}")

    # Keep a stable order while removing accidental duplicate selections.
    return list(dict.fromkeys(skills))
