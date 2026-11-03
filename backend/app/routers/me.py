from fastapi import APIRouter, Depends

from app.core.auth import CurrentUser, get_current_user
from app.db.repo import Repo
from app.deps import get_profile, get_repo
from app.schemas.models import ProfileOut, ProfileUpdate, TemplateOut

router = APIRouter(tags=["me"])


def _profile_out(profile: dict, email: str | None) -> ProfileOut:
    return ProfileOut(
        id=profile["id"],
        email=email,
        display_name=profile["display_name"],
        avatar_color=profile["avatar_color"],
        timezone=profile["timezone"],
        role=profile["role"],
    )


@router.get("/me", response_model=ProfileOut)
def read_me(user: CurrentUser = Depends(get_current_user), profile: dict = Depends(get_profile)):
    return _profile_out(profile, user.email)


@router.patch("/me", response_model=ProfileOut)
def update_me(
    body: ProfileUpdate,
    user: CurrentUser = Depends(get_current_user),
    profile: dict = Depends(get_profile),
    repo: Repo = Depends(get_repo),
):
    # Only these three fields are ever writable by the user; role is never accepted.
    fields = body.model_dump(exclude_none=True)
    updated = repo.update_profile(profile["id"], fields)
    return _profile_out(updated or profile, user.email)


@router.get("/templates", response_model=list[TemplateOut])
def list_templates(_: dict = Depends(get_profile), repo: Repo = Depends(get_repo)):
    return repo.list_templates()
