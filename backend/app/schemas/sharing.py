"""Request/response models for share links, friends and shared challenges."""

from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.models import DashboardOut, Streaks

Scope = Literal["achievements", "dashboard"]


# ---------------------------------------------------------------- public links
class ShareLinkCreate(BaseModel):
    scope: Scope
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def _future(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return v
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        if v <= datetime.now(UTC):
            raise ValueError("must be in the future")
        return v


class ShareLinkOut(BaseModel):
    id: UUID
    scope: Scope
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None


class ShareLinkCreated(ShareLinkOut):
    token: str  # returned only here, at creation
    path: str  # e.g. /s/<token>; the web app adds its own origin


class PublicBadge(BaseModel):
    code: str
    name: str
    stars: int
    earned_on: date


class SharedView(BaseModel):
    """What someone who is NOT the owner may see of a challenge. No email, ids or notes."""

    display_name: str
    challenge_name: str
    start_date: date
    end_date: date
    completion: float | None
    streaks: Streaks
    stars: int
    badges: list[PublicBadge]
    dashboard: DashboardOut | None = None


# ---------------------------------------------------------------- friends
class FriendRequestIn(BaseModel):
    email: str = Field(min_length=3, max_length=254)

    @field_validator("email")
    @classmethod
    def _looks_like_email(cls, v: str) -> str:
        v = v.strip().lower()
        local, _, domain = v.partition("@")
        if not local or "." not in domain or " " in v:
            raise ValueError("must be an email address")
        return v


class FriendOut(BaseModel):
    user_id: UUID
    display_name: str
    since: datetime | None


class IncomingRequestOut(BaseModel):
    id: UUID
    display_name: str
    created_at: datetime


class FriendsOut(BaseModel):
    friends: list[FriendOut]
    incoming: list[IncomingRequestOut]


class RequestAccepted(BaseModel):
    """The same answer whether or not the address has an account."""

    message: str = "If that person has an account, they will see your request."


# ---------------------------------------------------------------- shares with a friend
class ShareIn(BaseModel):
    friend_id: UUID


class ChallengeShareOut(BaseModel):
    friend_id: UUID
    display_name: str


class SharedChallengeOut(BaseModel):
    challenge_id: UUID
    name: str
    start_date: date
    end_date: date
    owner_display_name: str
    shared_at: datetime
