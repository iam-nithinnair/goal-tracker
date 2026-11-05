from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends

from app.core.errors import not_found
from app.db.repo import Repo
from app.deps import get_profile, get_repo
from app.schemas.models import DashboardOut
from app.services.dates import today_in
from app.services.scoring import compute_dashboard

router = APIRouter(tags=["dashboard"])


@router.get(
    "/challenges/{challenge_id}/dashboard",
    response_model=DashboardOut,
    response_model_by_alias=True,
)
def get_dashboard(
    challenge_id: UUID,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    challenge = repo.get_challenge(profile["id"], str(challenge_id))
    if challenge is None:
        raise not_found("Challenge")
    entries = repo.list_entries(str(challenge_id), None, None)
    out = compute_dashboard(
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
        today=today_in(profile["timezone"]),
    )
    for w in out["weeks"]:
        w["from_"] = w.pop("from")
    return out
