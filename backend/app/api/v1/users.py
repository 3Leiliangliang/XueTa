from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserProfile
from app.schemas.user import UserResponse, UserUpdateMeRequest


router = APIRouter()


@router.get("/me", response_model=UserResponse)
def current_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_current_user(
    payload: UserUpdateMeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    profile = current_user.profile
    if profile is None:
        profile = UserProfile(user_id=current_user.id)
        current_user.profile = profile

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.add(profile)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
