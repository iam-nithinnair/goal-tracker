"""Dashboard maths, implemented as docs/05-scoring-and-awards.md. Pure: no database, no clock.

Vocabulary: a *goal-day* is one goal on one day it is active. Each counted goal-day is Done,
Missed or N/A. Today's unlogged goal-days stay *pending* (counted nowhere); every earlier
unlogged goal-day is Missed.
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from statistics import fmean
from typing import Any

from app.services.dates import in_goal_window
from app.services.streaks import compute_streaks


def ratio(done: int, applicable: int) -> float | None:
    """Completion fraction, or None ("-" in the UI) when there is nothing to score."""
    return done / applicable if applicable else None


class _Tally:
    """Done / missed / N/A counts for any slice of goal-days."""

    __slots__ = ("done", "missed", "na")

    def __init__(self) -> None:
        self.done = self.missed = self.na = 0

    def add(self, status: str) -> None:
        if status == "yes":
            self.done += 1
        elif status == "na":
            self.na += 1
        else:
            self.missed += 1

    @property
    def applicable(self) -> int:
        return self.done + self.missed

    def out(self) -> dict[str, Any]:
        return {
            "done": self.done,
            "missed": self.missed,
            "na": self.na,
            "completion": ratio(self.done, self.applicable),
        }


def _month_key(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def _months_between(start: date, end: date) -> list[str]:
    keys, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        keys.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return keys


def compute_dashboard(
    *,
    start: date,
    end: date,
    goals: Iterable[Mapping[str, Any]],
    entries: Iterable[Mapping[str, Any]],
    today: date,
) -> dict[str, Any]:
    """Everything the dashboard shows. `goals` need id, name, active_from, active_to (dates);
    `entries` need goal_id, entry_date (date) and status."""
    goals = list(goals)
    logged = {(str(e["goal_id"]), e["entry_date"]): e["status"] for e in entries}
    as_of = min(today, end)
    total_days = (end - start).days + 1

    per_goal = {str(g["id"]): _Tally() for g in goals}
    per_month = {k: _Tally() for k in _months_between(start, end)}
    per_goal_month: dict[tuple[str, str], _Tally] = defaultdict(_Tally)
    weeks: dict[int, dict[str, Any]] = {}
    for n in range(1, (total_days - 1) // 7 + 2):
        first = start + timedelta(days=(n - 1) * 7)
        weeks[n] = {"tally": _Tally(), "from": first, "to": min(first + timedelta(days=6), end)}
    overall = _Tally()
    month_days: dict[str, list[dict[str, Any]]] = defaultdict(list)
    days: list[dict[str, Any]] = []

    day = start
    while day <= as_of:
        tally = _Tally()
        any_logged = False
        pending = 0
        for g in goals:
            gid = str(g["id"])
            if not in_goal_window(day, g["active_from"], g["active_to"]):
                continue
            status = logged.get((gid, day))
            if status is None:
                if day == today:
                    pending += 1
                    continue  # still pending: neither done nor missed
                status = "no"
            else:
                any_logged = True
            for t in (
                tally,
                overall,
                per_goal[gid],
                per_month[_month_key(day)],
                per_goal_month[(gid, _month_key(day))],
                weeks[(day - start).days // 7 + 1]["tally"],
            ):
                t.add(status)
        if day < today or any_logged:  # today only counts once something is logged on it
            record = {
                "date": day,
                "done": tally.done,
                "missed": tally.missed,
                "na": tally.na,
                "applicable": tally.applicable,
                "pending": pending,
                "score": ratio(tally.done, tally.applicable),
            }
            days.append(record)
            month_days[_month_key(day)].append(record)
        day += timedelta(days=1)

    def perfect(r: dict[str, Any]) -> bool:
        return r["applicable"] > 0 and r["done"] == r["applicable"] and r["pending"] == 0

    months = []
    for key, tally in per_month.items():
        rows = month_days.get(key, [])
        scores = [r["score"] for r in rows if r["score"] is not None]
        months.append(
            {
                "month": key,
                "days": len(rows),
                **tally.out(),
                "perfect_days": sum(perfect(r) for r in rows),
                "avg_daily_score": fmean(scores) if scores else None,
                "best_day": max(scores) if scores else None,
            }
        )

    days_in = len(days)
    return {
        "as_of": as_of,
        "kpis": {
            "total_days": total_days,
            "days_in": days_in,
            "days_left": total_days - days_in,
            "overall_completion": ratio(overall.done, overall.applicable),
            "perfect_days": sum(perfect(r) for r in days),
            "goals_completed": overall.done,
            "missed": overall.missed,
            "na": overall.na,
        },
        "goals": [
            {
                "goal_id": str(g["id"]),
                "name": g["name"],
                "retired": g["active_to"] is not None and g["active_to"] < as_of,
                **per_goal[str(g["id"])].out(),
            }
            for g in goals
        ],
        "streaks": compute_streaks(days, today),
        "months": months,
        "goal_months": [
            {"goal_id": gid, "month": month, **tally.out()}
            for (gid, month), tally in sorted(per_goal_month.items(), key=lambda kv: kv[0][1])
        ],
        "weeks": [
            {
                "week": n,
                "from": w["from"],
                "to": w["to"],
                "done": w["tally"].done,
                "possible": w["tally"].applicable,
                "completion": ratio(w["tally"].done, w["tally"].applicable),
            }
            for n, w in weeks.items()
        ],
        "days": days,
    }


def dashboard_for_challenge(
    challenge: Mapping[str, Any], entries: Iterable[Mapping[str, Any]], today: date
) -> dict[str, Any]:
    """`compute_dashboard` for a challenge row as the repository returns it (ISO-string dates)."""
    return compute_dashboard(
        start=date.fromisoformat(challenge["start_date"]),
        end=date.fromisoformat(challenge["end_date"]),
        goals=[
            {
                "id": g["id"],
                "name": g["name"],
                "active_from": date.fromisoformat(g["active_from"]),
                "active_to": date.fromisoformat(g["active_to"]) if g["active_to"] else None,
            }
            for g in challenge["goals"]
        ],
        entries=[{**e, "entry_date": date.fromisoformat(e["entry_date"])} for e in entries],
        today=today,
    )
