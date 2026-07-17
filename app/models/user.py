from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.models.enums import UserRole


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    """A simple demo identity. Authentication is not part of this MVP."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(min_length=1, max_length=100)
    role: UserRole
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
