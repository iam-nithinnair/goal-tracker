"""Date rules shared by the API (docs/05-scoring-and-awards.md, docs/04-api.md).

"Today" is always the user's own calendar day, never the server's.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def is_valid_timezone(name: str) -> bool:
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return False
    return True


def today_in(tz_name: str, now: datetime | None = None) -> date:
    """The calendar date right now in `tz_name` (falls back to UTC for unknown names)."""
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        tz = ZoneInfo("UTC")
    current = now if now is not None else datetime.now(tz=ZoneInfo("UTC"))
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return current.astimezone(tz).date()


def in_goal_window(day: date, active_from: date, active_to: date | None) -> bool:
    """A goal counts only between active_from and active_to (both inclusive)."""
    return day >= active_from and (active_to is None or day <= active_to)


def check_entry_date(
    day: date,
    *,
    today: date,
    challenge_start: date,
    challenge_end: date,
    active_from: date,
    active_to: date | None,
) -> str | None:
    """Return a human message if `day` cannot be logged, else None."""
    if day > today:
        return "You can't log a future day"
    if day < challenge_start or day > challenge_end:
        return "That date is outside the challenge"
    if not in_goal_window(day, active_from, active_to):
        return "That goal wasn't active on that date"
    return None
