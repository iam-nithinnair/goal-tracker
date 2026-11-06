from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.core.auth import CurrentUser, get_current_user
from app.core.errors import ApiError, not_found, validation_error
from app.db.repo import Repo
from app.deps import get_profile, get_repo
from app.schemas.sharing import (
    ChallengeShareOut,
    FriendOut,
    FriendRequestIn,
    FriendsOut,
    IncomingRequestOut,
    RequestAccepted,
    SharedChallengeOut,
    SharedView,
    ShareIn,
)
from app.services.share_view import build_view

router = APIRouter(tags=["friends"])

NO_CONTENT = status.HTTP_204_NO_CONTENT


def _other(row: dict, me: str) -> str:
    return row["addressee_id"] if row["requester_id"] == me else row["requester_id"]


def _accepted_friend_ids(repo: Repo, me: str) -> set[str]:
    return {_other(r, me) for r in repo.list_friendships(me) if r["status"] == "accepted"}


# ---------------------------------------------------------------- friends
@router.get("/friends", response_model=FriendsOut)
def list_friends(profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)):
    me = profile["id"]
    rows = repo.list_friendships(me)
    names = repo.profiles_by_ids([_other(r, me) for r in rows])
    # Requests you SENT are deliberately not listed: seeing one would reveal that the address you
    # typed belongs to an account.
    return FriendsOut(
        friends=[
            FriendOut(
                user_id=_other(r, me),
                display_name=names.get(_other(r, me), {}).get("display_name", "Someone"),
                since=r["responded_at"],
            )
            for r in rows
            if r["status"] == "accepted"
        ],
        incoming=[
            IncomingRequestOut(
                id=r["id"],
                display_name=names.get(r["requester_id"], {}).get("display_name", "Someone"),
                created_at=r["created_at"],
            )
            for r in rows
            if r["status"] == "pending" and r["addressee_id"] == me
        ],
    )


@router.post(
    "/friends/requests", response_model=RequestAccepted, status_code=status.HTTP_202_ACCEPTED
)
def send_request(
    body: FriendRequestIn,
    user: CurrentUser = Depends(get_current_user),
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    """Always answers the same way, so this cannot be used to discover who has an account."""
    if body.email == (user.email or "").lower():
        raise validation_error("You can't add yourself", {"email": "That's your own address"})
    target = repo.find_user_id_by_email(body.email)
    if target and target != profile["id"]:
        existing = repo.friendship_between(profile["id"], target)
        if existing is None:
            repo.create_friend_request(profile["id"], target)
        elif existing["status"] == "pending" and existing["addressee_id"] == profile["id"]:
            repo.accept_friendship(existing["id"])  # they had already asked you: that's a yes
    return RequestAccepted()


def _pending_for_me(repo: Repo, request_id: UUID, me: str) -> dict:
    row = repo.get_friendship(str(request_id))
    if row is None or row["addressee_id"] != me or row["status"] != "pending":
        raise not_found("Request")
    return row


@router.post("/friends/requests/{request_id}/accept", status_code=NO_CONTENT)
def accept_request(
    request_id: UUID, profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)
):
    repo.accept_friendship(_pending_for_me(repo, request_id, profile["id"])["id"])
    return Response(status_code=NO_CONTENT)


@router.post("/friends/requests/{request_id}/decline", status_code=NO_CONTENT)
def decline_request(
    request_id: UUID, profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)
):
    repo.delete_friendship(_pending_for_me(repo, request_id, profile["id"])["id"])
    return Response(status_code=NO_CONTENT)


@router.delete("/friends/{user_id}", status_code=NO_CONTENT)
def remove_friend(
    user_id: UUID, profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)
):
    """Unfriending also withdraws every challenge either of you had shared with the other."""
    row = repo.friendship_between(profile["id"], str(user_id))
    if row is None or row["status"] != "accepted":
        raise not_found("Friend")
    repo.delete_shares_between(profile["id"], str(user_id))
    repo.delete_friendship(row["id"])
    return Response(status_code=NO_CONTENT)


# ---------------------------------------------------------------- sharing a challenge
@router.get("/challenges/{challenge_id}/shares", response_model=list[ChallengeShareOut])
def list_shares(
    challenge_id: UUID, profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)
):
    if repo.get_challenge(profile["id"], str(challenge_id)) is None:
        raise not_found("Challenge")
    rows = repo.list_shares(str(challenge_id))
    names = repo.profiles_by_ids([r["friend_id"] for r in rows])
    return [
        ChallengeShareOut(
            friend_id=r["friend_id"],
            display_name=names.get(r["friend_id"], {}).get("display_name", "Someone"),
        )
        for r in rows
    ]


@router.post(
    "/challenges/{challenge_id}/shares",
    response_model=ChallengeShareOut,
    status_code=status.HTTP_201_CREATED,
)
def share_with_friend(
    challenge_id: UUID,
    body: ShareIn,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    if repo.get_challenge(profile["id"], str(challenge_id)) is None:
        raise not_found("Challenge")
    friend = str(body.friend_id)
    if friend not in _accepted_friend_ids(repo, profile["id"]):
        raise ApiError(409, "not_friends", "You can only share with people you are friends with")
    repo.create_share(str(challenge_id), profile["id"], friend)
    name = repo.profiles_by_ids([friend]).get(friend, {}).get("display_name", "Someone")
    return ChallengeShareOut(friend_id=body.friend_id, display_name=name)


@router.delete("/challenges/{challenge_id}/shares/{friend_id}", status_code=NO_CONTENT)
def unshare(
    challenge_id: UUID,
    friend_id: UUID,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    if repo.get_challenge(profile["id"], str(challenge_id)) is None:
        raise not_found("Challenge")
    repo.delete_share(str(challenge_id), str(friend_id))
    return Response(status_code=NO_CONTENT)


# ---------------------------------------------------------------- what friends shared with me
@router.get("/shared-with-me", response_model=list[SharedChallengeOut])
def shared_with_me(profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)):
    me = profile["id"]
    friends = _accepted_friend_ids(repo, me)
    rows = [r for r in repo.list_shared_with(me) if r["owner_id"] in friends and r["challenges"]]
    names = repo.profiles_by_ids([r["owner_id"] for r in rows])
    return [
        SharedChallengeOut(
            challenge_id=r["challenges"]["id"],
            name=r["challenges"]["name"],
            start_date=r["challenges"]["start_date"],
            end_date=r["challenges"]["end_date"],
            owner_display_name=names.get(r["owner_id"], {}).get("display_name", "Someone"),
            shared_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/shared-with-me/{challenge_id}/dashboard", response_model=SharedView)
def shared_dashboard(
    challenge_id: UUID, profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)
):
    """Read-only: there is no write route under /shared-with-me, and the owner-scoped write
    routes elsewhere 404 for anyone but the owner."""
    share = repo.get_share(str(challenge_id), profile["id"])
    if share is None or share["owner_id"] not in _accepted_friend_ids(repo, profile["id"]):
        raise not_found("Challenge")
    challenge = repo.get_challenge_by_id(str(challenge_id))
    owner = repo.get_profile(share["owner_id"])
    if challenge is None or owner is None:
        raise not_found("Challenge")
    return build_view(repo, challenge, owner, with_dashboard=True)
