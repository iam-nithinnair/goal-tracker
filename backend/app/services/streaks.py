"""Streaks (docs/05-scoring-and-awards.md#streaks). Pure functions over the per-day rows
`compute_dashboard` produces."""

from collections.abc import Iterable, Mapping
from datetime import date
from typing import Any

SUCCESS_THRESHOLD = 0.8  # a day with a score of at least 80% extends the day streak


def _runs(days: Iterable[Mapping[str, Any]], today: date, ok: Any) -> tuple[int, int]:
    """(current, longest) run of days where ok(day) holds.

    A day with nothing applicable is neutral: it neither extends nor breaks a run. Today is
    still being lived, so a today that is not (yet) good is skipped rather than breaking it.
    """
    current = longest = 0
    for d in days:
        if d["applicable"] == 0:
            continue
        if ok(d):
            current += 1
            longest = max(longest, current)
        elif d["date"] == today:
            continue
        else:
            current = 0
    return current, longest


def compute_streaks(
    days: Iterable[Mapping[str, Any]], today: date, threshold: float = SUCCESS_THRESHOLD
) -> dict[str, int]:
    days = list(days)
    current, longest = _runs(
        days, today, lambda d: d["score"] is not None and d["score"] >= threshold
    )
    p_current, p_longest = _runs(
        days, today, lambda d: d["done"] == d["applicable"] and d.get("pending", 0) == 0
    )
    return {
        "current": current,
        "longest": longest,
        "perfect_current": p_current,
        "perfect_longest": p_longest,
    }
