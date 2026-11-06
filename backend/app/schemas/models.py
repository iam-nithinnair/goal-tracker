"""Request/response models. Field rules mirror docs/01-product-requirements.md."""

import re
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.services.dates import is_valid_timezone

Status = Literal["yes", "no", "na"]
MAX_CHALLENGE_DAYS = 366
_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _clean_name(value: str, max_len: int) -> str:
    value = value.strip()
    if not 1 <= len(value) <= max_len:
        raise ValueError(f"must be 1-{max_len} characters")
    return value


# ---------------------------------------------------------------- profile
class ProfileOut(BaseModel):
    id: UUID
    email: str | None = None
    display_name: str
    avatar_color: str
    timezone: str
    role: str


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    avatar_color: str | None = None
    timezone: str | None = None

    @field_validator("display_name")
    @classmethod
    def _name(cls, v: str | None) -> str | None:
        return None if v is None else _clean_name(v, 50)

    @field_validator("avatar_color")
    @classmethod
    def _color(cls, v: str | None) -> str | None:
        if v is not None and not _COLOR.match(v):
            raise ValueError("must be a hex colour like #7c9cff")
        return v

    @field_validator("timezone")
    @classmethod
    def _tz(cls, v: str | None) -> str | None:
        if v is not None and not is_valid_timezone(v):
            raise ValueError("unknown timezone")
        return v


# ---------------------------------------------------------------- goals
class GoalOut(BaseModel):
    id: UUID
    challenge_id: UUID
    name: str
    position: int
    active_from: date
    active_to: date | None = None


class GoalCreate(BaseModel):
    name: str
    position: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        return _clean_name(v, 80)


class GoalUpdate(BaseModel):
    name: str | None = None
    position: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str | None) -> str | None:
        return None if v is None else _clean_name(v, 80)


class GoalOrder(BaseModel):
    goal_ids: list[UUID] = Field(min_length=1, max_length=100)


class RetireBody(BaseModel):
    on: date


# ---------------------------------------------------------------- challenges
class ChallengeOut(BaseModel):
    id: UUID
    name: str
    start_date: date
    end_date: date
    status: str
    is_template: bool = False
    created_at: datetime | None = None


class ChallengeDetail(ChallengeOut):
    goals: list[GoalOut] = []


class ChallengeCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    template_id: UUID | None = None
    goals: list[str] = Field(default_factory=list, max_length=50)

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        return _clean_name(v, 80)

    @field_validator("goals")
    @classmethod
    def _goals(cls, v: list[str]) -> list[str]:
        return [_clean_name(g, 80) for g in v]

    @model_validator(mode="after")
    def _dates(self) -> "ChallengeCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if (self.end_date - self.start_date).days + 1 > MAX_CHALLENGE_DAYS:
            raise ValueError(f"a challenge can last at most {MAX_CHALLENGE_DAYS} days")
        return self


class ChallengeUpdate(BaseModel):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: Literal["active", "archived"] | None = None

    @field_validator("name")
    @classmethod
    def _name(cls, v: str | None) -> str | None:
        return None if v is None else _clean_name(v, 80)


class TemplateOut(BaseModel):
    id: UUID
    name: str
    start_date: date
    end_date: date
    goals: list[GoalOut]


# ---------------------------------------------------------------- entries
class EntryOut(BaseModel):
    goal_id: UUID
    entry_date: date
    status: Status


class EntryPut(BaseModel):
    status: Status


class DayEntry(BaseModel):
    goal_id: UUID
    status: Status


class DayPut(BaseModel):
    entries: list[DayEntry] = Field(min_length=1, max_length=100)


class BadgeOut(BaseModel):
    code: str
    name: str
    description: str
    stars: int


class EntryWriteResult(BaseModel):
    entries: list[EntryOut]
    new_badges: list[BadgeOut] = []


# ---------------------------------------------------------------- dashboard
class Counts(BaseModel):
    done: int
    missed: int
    na: int
    completion: float | None  # None = nothing to score yet ("-")


class DashboardKpis(BaseModel):
    total_days: int
    days_in: int
    days_left: int
    overall_completion: float | None
    perfect_days: int
    goals_completed: int
    missed: int
    na: int


class GoalStats(Counts):
    goal_id: str
    name: str
    retired: bool


class MonthStats(Counts):
    month: str  # YYYY-MM
    days: int
    perfect_days: int
    avg_daily_score: float | None
    best_day: float | None


class GoalMonthStats(Counts):
    goal_id: str
    month: str


class WeekStats(BaseModel):
    week: int
    from_: date = Field(serialization_alias="from")
    to: date
    done: int
    possible: int
    completion: float | None

    model_config = {"populate_by_name": True}


class DayStats(BaseModel):
    date: date
    done: int
    missed: int
    na: int
    applicable: int
    pending: int
    score: float | None


class Streaks(BaseModel):
    current: int
    longest: int
    perfect_current: int
    perfect_longest: int


class DashboardOut(BaseModel):
    as_of: date
    kpis: DashboardKpis
    streaks: Streaks
    goals: list[GoalStats]
    months: list[MonthStats]
    goal_months: list[GoalMonthStats]
    weeks: list[WeekStats]
    days: list[DayStats]


# ---------------------------------------------------------------- awards
class EarnedOut(BaseModel):
    challenge_id: UUID
    challenge_name: str
    earned_on: date


class BadgeStatus(BadgeOut):
    earned_on: date | None  # first time it was earned (None = still locked)
    earned: list[EarnedOut]  # every challenge it was earned in


class ChallengeStars(BaseModel):
    challenge_id: UUID
    name: str
    stars: int
    badges: int


class StarsOut(BaseModel):
    total_stars: int
    by_challenge: list[ChallengeStars]
