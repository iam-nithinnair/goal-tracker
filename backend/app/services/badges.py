"""Badge rules (docs/05-scoring-and-awards.md#stars-and-awards). Pure: given a computed dashboard
it says which badges are currently earned. Persisting them (idempotently, never revoking) is the
caller's job, so evaluating twice, or after history is edited, can never take a badge away.
"""

import calendar
from collections.abc import Mapping
from datetime import date
from typing import Any

from app.services.streaks import compute_streaks

# Used when a catalogue row has no (or a partial) `rule`, so a missing key can't break evaluation.
DEFAULT_RULES: dict[str, dict[str, Any]] = {
    "STREAK_3": {"days": 3},
    "STREAK_7": {"days": 7},
    "STREAK_14": {"days": 14},
    "STREAK_30": {"days": 30},
    "WEEK_80": {"completion": 0.8},
    "MONTH_80": {"completion": 0.8},
    "GOAL_MASTER": {"completion": 0.9, "min_days": 14},
    "COMEBACK": {"low_days": 3},
    "CHALLENGE_COMPLETE": {"completion": 0.6},
    "CHALLENGE_CHAMPION": {"completion": 0.9},
}
GOOD_DAY = 0.8  # a "good" day, shared with the streak rule
LOW_DAY = 0.5


def _rule(rules: Mapping[str, Mapping[str, Any]], code: str) -> dict[str, Any]:
    return {**DEFAULT_RULES.get(code, {}), **(rules.get(code) or {})}


def earned_codes(
    dash: Mapping[str, Any],
    *,
    entry_count: int,
    start: date,
    end: date,
    today: date,
    rules: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[str]:
    """Codes of every badge whose rule is met by this challenge as of `today`."""
    rules = rules or {}
    out: list[str] = []
    # A day with goals still to log can change; only settled days can earn a badge.
    settled = [d for d in dash["days"] if d["pending"] == 0]

    if entry_count > 0:
        out.append("FIRST_LOG")

    if any(d["applicable"] > 0 and d["done"] == d["applicable"] for d in settled):
        out.append("FIRST_PERFECT_DAY")

    longest = compute_streaks(settled, today)["longest"]
    for code in ("STREAK_3", "STREAK_7", "STREAK_14", "STREAK_30"):
        if longest >= _rule(rules, code)["days"]:
            out.append(code)

    # Weeks and months only count once they are over, so a lucky first day can't earn them.
    week_min = _rule(rules, "WEEK_80")["completion"]
    if any(
        w["to"] < today and w["possible"] > 0 and w["completion"] >= week_min for w in dash["weeks"]
    ):
        out.append("WEEK_80")

    month_min = _rule(rules, "MONTH_80")["completion"]
    for m in dash["months"]:
        year, mon = (int(p) for p in m["month"].split("-"))
        last_day = min(date(year, mon, calendar.monthrange(year, mon)[1]), end)
        if m["days"] > 0 and last_day < today and m["completion"] >= month_min:
            out.append("MONTH_80")
            break

    master = _rule(rules, "GOAL_MASTER")
    if any(
        g["done"] + g["missed"] >= master["min_days"] and g["completion"] >= master["completion"]
        for g in dash["goals"]
    ):
        out.append("GOAL_MASTER")

    low_days = _rule(rules, "COMEBACK")["low_days"]
    low_run = 0
    for d in settled:
        if d["score"] is None:
            continue
        if d["score"] >= GOOD_DAY and low_run >= low_days:
            out.append("COMEBACK")
            break
        low_run = low_run + 1 if d["score"] < LOW_DAY else 0

    total_days = (end - start).days + 1
    if today >= start and (min(today, end) - start).days + 1 >= total_days / 2:
        out.append("HALFWAY")

    if today > end:
        overall = dash["kpis"]["overall_completion"]
        if overall is not None and overall >= _rule(rules, "CHALLENGE_COMPLETE")["completion"]:
            out.append("CHALLENGE_COMPLETE")
        if overall is not None and overall >= _rule(rules, "CHALLENGE_CHAMPION")["completion"]:
            out.append("CHALLENGE_CHAMPION")

    return out
