from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.errors import ApiError, not_found, validation_error
from app.db.repo import Repo
from app.deps import get_profile, get_repo
from app.schemas.models import GoalOut, GoalUpdate, RetireBody

router = APIRouter(tags=["goals"])


def _owned_goal(repo: Repo, profile: dict, goal_id: UUID) -> dict:
    goal = repo.get_goal(profile["id"], str(goal_id))
    if goal is None:
        raise not_found("Goal")
    return goal


@router.patch("/goals/{goal_id}", response_model=GoalOut)
def update_goal(
    goal_id: UUID,
    body: GoalUpdate,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    goal = _owned_goal(repo, profile, goal_id)
    return repo.update_goal(goal["id"], body.model_dump(exclude_none=True))


@router.post("/goals/{goal_id}/retire", response_model=GoalOut)
def retire_goal(
    goal_id: UUID,
    body: RetireBody,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    """`on` is the LAST day the goal counts. Earlier history is untouched."""
    goal = _owned_goal(repo, profile, goal_id)
    last_day = date.fromisoformat(goal["challenges"]["end_date"])
    first_day = date.fromisoformat(goal["active_from"])
    if body.on < first_day or body.on > last_day:
        raise validation_error(
            "Retire date must fall between the goal's first day and the challenge end",
            {"on": "out of range"},
        )
    return repo.update_goal(goal["id"], {"active_to": body.on.isoformat()})


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: UUID,
    confirm: bool = False,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    goal = _owned_goal(repo, profile, goal_id)
    if not confirm:
        raise ApiError(
            400,
            "confirmation_required",
            "Deleting a goal also deletes its history. Retire it instead, or pass confirm=true.",
        )
    repo.delete_goal(goal["id"])
