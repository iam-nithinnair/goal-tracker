from fastapi import Depends

from app.core.auth import CurrentUser, get_current_user
from app.core.errors import ApiError
from app.db.repo import Repo, get_client


def get_repo() -> Repo:
    return Repo(get_client())


def get_profile(
    user: CurrentUser = Depends(get_current_user), repo: Repo = Depends(get_repo)
) -> dict:
    """The caller's profile. Disabled accounts are refused everywhere."""
    profile = repo.get_profile(user.id)
    if profile is None:
        raise ApiError(401, "unauthorized", "No profile for this account")
    if profile["is_disabled"]:
        raise ApiError(403, "account_disabled", "This account has been disabled")
    return profile
