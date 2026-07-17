from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "STUDENT"
    PROJECT_OWNER = "PROJECT_OWNER"


class WorkType(StrEnum):
    REMOTE = "REMOTE"
    ON_SITE = "ON_SITE"


class WorkPreference(StrEnum):
    REMOTE = "REMOTE"
    ON_SITE = "ON_SITE"
    BOTH = "BOTH"


class ProjectStatus(StrEnum):
    OPEN = "OPEN"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


class InvitationStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
