from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from app.core.errors import ApiError, not_found
from app.db.repo import Repo
from app.deps import get_profile, get_repo
from app.schemas.sharing import SharedView, ShareLinkCreate, ShareLinkCreated, ShareLinkOut
from app.services.share_view import build_view
from app.services.sharing import RateLimiter, hash_token, new_token

router = APIRouter(tags=["sharing"])

# 30 public lookups a minute per client. Guessing a 256-bit token is hopeless anyway; this stops
# someone hammering the endpoint.
public_limiter = RateLimiter(limit=30, window_s=60)
MAX_TOKEN_LEN = 64  # tokens are 43 characters; anything longer cannot be one


@router.post(
    "/challenges/{challenge_id}/share-links",
    response_model=ShareLinkCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_link(
    challenge_id: UUID,
    body: ShareLinkCreate,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    if repo.get_challenge(profile["id"], str(challenge_id)) is None:
        raise not_found("Challenge")
    token = new_token()
    row = repo.create_share_link(
        profile["id"],
        str(challenge_id),
        body.scope,
        body.expires_at.isoformat() if body.expires_at else None,
        hash_token(token),
    )
    return ShareLinkCreated(**row, token=token, path=f"/s/{token}")


@router.get("/challenges/{challenge_id}/share-links", response_model=list[ShareLinkOut])
def list_links(
    challenge_id: UUID,
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    if repo.get_challenge(profile["id"], str(challenge_id)) is None:
        raise not_found("Challenge")
    return repo.list_share_links(str(challenge_id))


@router.delete("/share-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_link(
    link_id: UUID, profile: dict = Depends(get_profile), repo: Repo = Depends(get_repo)
):
    if not repo.revoke_share_link(profile["id"], str(link_id)):
        raise not_found("Share link")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/public/share/{token}", response_model=SharedView)
def public_share(token: str, request: Request, repo: Repo = Depends(get_repo)):
    """No login. Unknown, revoked and expired tokens are all the same 404."""
    client = request.client.host if request.client else "unknown"
    if not public_limiter.allow(client):
        raise ApiError(429, "rate_limited", "Too many requests, try again in a minute")

    link = repo.get_share_link_by_hash(hash_token(token)) if len(token) <= MAX_TOKEN_LEN else None
    gone = (
        link is None
        or link["revoked_at"] is not None
        or (link["expires_at"] and datetime.fromisoformat(link["expires_at"]) <= datetime.now(UTC))
    )
    challenge = None if gone else repo.get_challenge_by_id(link["challenge_id"])
    owner = repo.get_profile(link["owner_id"]) if challenge else None
    if challenge is None or owner is None or owner["is_disabled"]:
        raise not_found("Share link")
    return build_view(repo, challenge, owner, with_dashboard=link["scope"] == "dashboard")
