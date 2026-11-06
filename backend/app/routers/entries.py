from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.errors import not_found, validation_error
from app.db.repo import Repo
from app.deps import get_profile, get_repo
from app.schemas.models import DayPut, EntryOut, EntryPut, EntryWriteResult
from app.services.awards import evaluate_after_write
from app.services.dates import check_entry_date, today_in

router = APIRouter(tags=["entries"])


def _check(goal: dict, day: date, profile: dict) -> None:
    ch = goal["challenges"]
    problem = check_entry_date(
        day,
        today=today_in(profile["timezone"]),
        challenge_start=date.fromisoformat(ch["start_date"]),
        challenge_end=date.fromisoformat(ch["end_date"]),
        active_from=date.fromisoformat(goal["active_from"]),
        active_to=date.fromisoformat(goal["active_to"]) if goal["active_to"] else None,
    )
    if problem:
        raise validation_error(problem, {"date": problem})


@router.get("/challenges/{challenge_id}/entries", response_model=list[EntryOut])
def list_entries(
    challenge_id: UUID,
    from_: date | None = Query(default=None, alias="from"),
    to: date | None = None,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    if repo.get_challenge(profile["id"], str(challenge_id)) is None:
        raise not_found("Challenge")
    return repo.list_entries(str(challenge_id), from_, to)


@router.put("/goals/{goal_id}/entries/{day}", response_model=EntryWriteResult)
def put_entry(
    goal_id: UUID,
    day: date,
    body: EntryPut,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    goal = repo.get_goal(profile["id"], str(goal_id))
    if goal is None:
        raise not_found("Goal")
    _check(goal, day, profile)
    saved = repo.upsert_entries(
        [{"goal_id": str(goal_id), "entry_date": day.isoformat(), "status": body.status}]
    )
    new = evaluate_after_write(
        repo, profile["id"], goal["challenge_id"], today_in(profile["timezone"])
    )
    return EntryWriteResult(entries=saved, new_badges=new)


@router.put("/challenges/{challenge_id}/entries/{day}", response_model=EntryWriteResult)
def put_day(
    challenge_id: UUID,
    day: date,
    body: DayPut,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    challenge = repo.get_challenge(profile["id"], str(challenge_id))
    if challenge is None:
        raise not_found("Challenge")
    goals = {g["id"]: g for g in challenge["goals"]}
    rows = []
    for e in body.entries:
        goal = goals.get(str(e.goal_id))
        if goal is None:
            raise not_found("Goal")
        _check({**goal, "challenges": challenge}, day, profile)
        rows.append({"goal_id": str(e.goal_id), "entry_date": day.isoformat(), "status": e.status})
    saved = repo.upsert_entries(rows)
    new = evaluate_after_write(
        repo, profile["id"], str(challenge_id), today_in(profile["timezone"])
    )
    return EntryWriteResult(entries=saved, new_badges=new)


@router.delete("/goals/{goal_id}/entries/{day}", status_code=status.HTTP_204_NO_CONTENT)
def clear_entry(
    goal_id: UUID,
    day: date,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    goal = repo.get_goal(profile["id"], str(goal_id))
    if goal is None:
        raise not_found("Goal")
    repo.delete_entry(str(goal_id), day)
