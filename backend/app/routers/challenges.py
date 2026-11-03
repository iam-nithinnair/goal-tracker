from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.errors import ApiError, not_found, validation_error
from app.db.repo import Repo
from app.deps import get_profile, get_repo
from app.schemas.models import (
    MAX_CHALLENGE_DAYS,
    ChallengeCreate,
    ChallengeDetail,
    ChallengeOut,
    ChallengeUpdate,
    GoalCreate,
    GoalOrder,
    GoalOut,
)

router = APIRouter(tags=["challenges"])


def _owned(repo: Repo, profile: dict, challenge_id: UUID) -> dict:
    challenge = repo.get_challenge(profile["id"], str(challenge_id))
    if challenge is None:
        raise not_found("Challenge")
    return challenge


@router.get("/challenges", response_model=list[ChallengeOut])
def list_challenges(
    status_filter: Literal["active", "archived"] | None = Query(default=None, alias="status"),
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    return repo.list_challenges(profile["id"], status_filter)


@router.post("/challenges", response_model=ChallengeDetail, status_code=status.HTTP_201_CREATED)
def create_challenge(
    body: ChallengeCreate, profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)
):
    goal_names: list[str] = []
    if body.template_id:
        template = repo.get_template(str(body.template_id))
        if template is None:
            raise not_found("Template")
        goal_names = [g["name"] for g in template["goals"]]
    goal_names += body.goals
    return repo.create_challenge(
        profile["id"], body.name, body.start_date, body.end_date, goal_names
    )


@router.get("/challenges/{challenge_id}", response_model=ChallengeDetail)
def get_challenge(
    challenge_id: UUID, profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)
):
    return _owned(repo, profile, challenge_id)


@router.patch("/challenges/{challenge_id}", response_model=ChallengeDetail)
def update_challenge(
    challenge_id: UUID,
    body: ChallengeUpdate,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    challenge = _owned(repo, profile, challenge_id)
    fields = body.model_dump(exclude_none=True)

    old_start = date.fromisoformat(challenge["start_date"])
    old_end = date.fromisoformat(challenge["end_date"])
    new_start = body.start_date or old_start
    new_end = body.end_date or old_end

    if new_end < new_start:
        raise validation_error("end_date must be on or after start_date", {"end_date": "too early"})
    if (new_end - new_start).days + 1 > MAX_CHALLENGE_DAYS:
        raise validation_error(f"A challenge can last at most {MAX_CHALLENGE_DAYS} days")

    dates_changed = (new_start, new_end) != (old_start, old_end)
    if dates_changed:
        first, last = repo.entry_date_bounds(challenge["id"])
        if (first and new_start > first) or (last and new_end < last):
            raise ApiError(
                409,
                "dates_exclude_entries",
                "Those dates would leave days you've already logged outside the challenge",
            )
        fields["start_date"] = new_start.isoformat()
        fields["end_date"] = new_end.isoformat()

    repo.update_challenge(challenge["id"], fields)
    if dates_changed:
        repo.realign_goals_to_dates(challenge["id"], old_start, new_start, new_end)
    return _owned(repo, profile, challenge_id)


@router.delete("/challenges/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_challenge(
    challenge_id: UUID,
    confirm: bool = False,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    challenge = _owned(repo, profile, challenge_id)
    if not confirm:
        raise ApiError(
            400,
            "confirmation_required",
            "Deleting a challenge removes all its data. Pass confirm=true.",
        )
    repo.delete_challenge(challenge["id"])


@router.post(
    "/challenges/{challenge_id}/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED
)
def add_goal(
    challenge_id: UUID,
    body: GoalCreate,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    challenge = _owned(repo, profile, challenge_id)
    if len(challenge["goals"]) >= 50:
        raise validation_error("A challenge can have at most 50 goals")
    return repo.add_goal(challenge, body.name, body.position)


@router.put("/challenges/{challenge_id}/goals/order", response_model=list[GoalOut])
def reorder_goals(
    challenge_id: UUID,
    body: GoalOrder,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    challenge = _owned(repo, profile, challenge_id)
    existing = {g["id"] for g in challenge["goals"]}
    requested = [str(g) for g in body.goal_ids]
    if len(set(requested)) != len(requested) or set(requested) != existing:
        raise validation_error("goal_ids must list every goal of this challenge exactly once")
    repo.reorder_goals(requested)
    return _owned(repo, profile, challenge_id)["goals"]
