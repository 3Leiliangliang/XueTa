from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=6, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_register_data(self) -> "RegisterRequest":
        if not self.email and not self.phone:
            raise ValueError("Either email or phone is required")
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class PasswordLoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class SendCodeRequest(BaseModel):
    target: str = Field(min_length=3, max_length=255)
    channel: str = Field(default="sms", max_length=32)
    purpose: str = Field(default="login", max_length=64)


class CodeLoginRequest(BaseModel):
    target: str = Field(min_length=3, max_length=255)
    code: str = Field(min_length=4, max_length=12)
    channel: str = Field(default="sms", max_length=32)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=16, max_length=512)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_passwords(self) -> "ResetPasswordRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=16, max_length=512)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class SendCodeResponse(BaseModel):
    success: bool = True
    message: str
    expires_at: datetime
    debug_code: str | None = None


class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str
    reset_token: str | None = None
