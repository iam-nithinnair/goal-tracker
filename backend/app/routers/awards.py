import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query

from app.core.config import get_settings
from app.core.errors import not_found
from app.db.repo import Repo
from app.deps import get_profile, get_repo
from app.schemas.models import BadgeStatus, ChallengeStars, StarsOut
from app.services.awards import evaluate_challenge
from app.services.dates import today_in

router = APIRouter(tags=["awards"])


def _catch_up(repo: Repo, profile: dict) -> None:
    """Award time-based badges (halfway, challenge complete) that became true without a check-in.
    Cheap enough to run when someone views their awards; the nightly job covers everyone else."""
    today = today_in(profile["timezone"])
    for c in repo.list_challenges(profile["id"], "active"):
        challenge = repo.get_challenge(profile["id"], c["id"])
        if challenge:
            evaluate_challenge(repo, profile["id"], challenge, today)


@router.get("/badges", response_model=list[BadgeStatus])
def list_badges(
    challenge_id: UUID | None = Query(default=None),
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    if challenge_id and repo.get_challenge(profile["id"], str(challenge_id)) is None:
        raise not_found("Challenge")
    _catch_up(repo, profile)
    earned: dict[str, list[dict]] = {}
    for row in repo.earned_badges(profile["id"], str(challenge_id) if challenge_id else None):
        earned.setdefault(row["badge_code"], []).append(
            {
                "challenge_id": row["challenge_id"],
                "challenge_name": (row.get("challenges") or {}).get("name", ""),
                "earned_on": row["earned_on"],
            }
        )
    return [
        {
            "code": b["code"],
            "name": b["name"],
            "description": b["description"],
            "stars": b["stars"],
            "earned_on": earned[b["code"]][0]["earned_on"] if b["code"] in earned else None,
            "earned": earned.get(b["code"], []),
        }
        for b in repo.list_badges()
    ]


@router.get("/me/stars", response_model=StarsOut)
def my_stars(profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)):
    _catch_up(repo, profile)
    stars = {b["code"]: b["stars"] for b in repo.list_badges()}
    per: dict[str, dict] = {}
    for row in repo.earned_badges(profile["id"]):
        entry = per.setdefault(
            row["challenge_id"],
            {
                "challenge_id": row["challenge_id"],
                "name": (row.get("challenges") or {}).get("name", ""),
                "stars": 0,
                "badges": 0,
            },
        )
        entry["stars"] += stars.get(row["badge_code"], 0)
        entry["badges"] += 1
    by_challenge = [ChallengeStars(**v) for v in per.values()]
    return StarsOut(total_stars=sum(c.stars for c in by_challenge), by_challenge=by_challenge)


@router.post("/internal/jobs/awards", include_in_schema=False)
def awards_job(x_job_secret: str | None = Header(default=None), repo: Repo = Depends(get_repo)):
    """Nightly catch-up for time-based badges, for everyone. Off unless JOB_SECRET is configured,
    and indistinguishable from a missing route otherwise."""
    secret = get_settings().job_secret
    if not secret or not x_job_secret or not hmac.compare_digest(secret, x_job_secret):
        raise not_found("Route")
    awarded = 0
    for c in repo.active_challenges_with_owners():
        owner = c.pop("profiles", None)
        if not owner or owner["is_disabled"]:
            continue
        awarded += len(evaluate_challenge(repo, owner["id"], c, today_in(owner["timezone"])))
    return {"awarded": awarded}
