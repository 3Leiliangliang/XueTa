from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.user import UserStatus


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str | None = None
    avatar_url: str | None = None
    grade_level: str | None = None
    target_exam: str | None = None
    preferred_subjects: str | None = None
    learning_style: str | None = None
    bio: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr | None = None
    phone: str | None = None
    username: str
    status: UserStatus
    email_verified: bool
    phone_verified: bool
    profile: UserProfileResponse | None = None


class UserUpdateMeRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=128)
    avatar_url: str | None = Field(default=None, max_length=512)
    grade_level: str | None = Field(default=None, max_length=64)
    target_exam: str | None = Field(default=None, max_length=128)
    preferred_subjects: str | None = None
    learning_style: str | None = Field(default=None, max_length=128)
    bio: str | None = None

    @model_validator(mode="after")
    def ensure_at_least_one_field(self) -> "UserUpdateMeRequest":
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("At least one profile field must be provided")
        return self


class UserProfileUpdatePayload(BaseModel):
    profile: dict[str, Any]
