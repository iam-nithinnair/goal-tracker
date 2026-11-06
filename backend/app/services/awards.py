"""Glue between the pure badge rules and the database: evaluate a challenge, record anything new."""

import logging
from datetime import date
from typing import Any

from app.db.repo import Repo
from app.services.badges import earned_codes
from app.services.scoring import dashboard_for_challenge

log = logging.getLogger("goal_tracker")


def evaluate_challenge(
    repo: Repo, user_id: str, challenge: dict[str, Any], today: date
) -> list[dict[str, Any]]:
    """Award every badge this challenge now qualifies for and return the NEWLY earned ones
    (catalogue rows). Idempotent: running it again returns nothing, and nothing is ever revoked."""
    catalogue = repo.list_badges()
    entries = repo.list_entries(challenge["id"], None, None)
    dash = dashboard_for_challenge(challenge, entries, today)
    codes = earned_codes(
        dash,
        entry_count=len(entries),
        start=date.fromisoformat(challenge["start_date"]),
        end=date.fromisoformat(challenge["end_date"]),
        today=today,
        rules={b["code"]: b["rule"] for b in catalogue},
    )
    live = {b["code"] for b in catalogue}
    new = set(repo.award_badges(user_id, challenge["id"], [c for c in codes if c in live], today))
    return [b for b in catalogue if b["code"] in new]


def evaluate_after_write(
    repo: Repo, user_id: str, challenge_id: str, today: date
) -> list[dict[str, Any]]:
    """Used by entry writes. A badge problem must never lose the check-in, so it only logs."""
    try:
        challenge = repo.get_challenge(user_id, challenge_id)
        return evaluate_challenge(repo, user_id, challenge, today) if challenge else []
    except Exception:
        log.exception("badge evaluation failed for challenge %s", challenge_id)
        return []
