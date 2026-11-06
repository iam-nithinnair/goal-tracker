"""The read-only view of a challenge shown through a public link or to a friend."""

from typing import Any

from app.db.repo import Repo
from app.services.dates import today_in
from app.services.scoring import dashboard_for_challenge


def _anonymise_goal_ids(dash: dict[str, Any]) -> dict[str, Any]:
    """Replace goal UUIDs with local keys so a viewer gets nothing that could be looked up."""
    keys = {g["goal_id"]: f"g{i + 1}" for i, g in enumerate(dash["goals"])}
    for row in (*dash["goals"], *dash["goal_months"]):
        row["goal_id"] = keys[row["goal_id"]]
    return dash


def build_view(
    repo: Repo, challenge: dict[str, Any], owner: dict[str, Any], *, with_dashboard: bool
) -> dict[str, Any]:
    entries = repo.list_entries(challenge["id"], None, None)
    dash = dashboard_for_challenge(challenge, entries, today_in(owner["timezone"]))
    catalogue = {b["code"]: b for b in repo.list_badges()}
    badges = [
        {
            "code": row["badge_code"],
            "name": catalogue[row["badge_code"]]["name"],
            "stars": catalogue[row["badge_code"]]["stars"],
            "earned_on": row["earned_on"],
        }
        for row in repo.earned_badges(owner["id"], challenge["id"])
        if row["badge_code"] in catalogue
    ]
    for w in dash["weeks"]:
        w["from_"] = w.pop("from")
    return {
        "display_name": owner["display_name"],
        "challenge_name": challenge["name"],
        "start_date": challenge["start_date"],
        "end_date": challenge["end_date"],
        "completion": dash["kpis"]["overall_completion"],
        "streaks": dash["streaks"],
        "stars": sum(b["stars"] for b in badges),
        "badges": badges,
        "dashboard": _anonymise_goal_ids(dash) if with_dashboard else None,
    }
