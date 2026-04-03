from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import (
    CodeLoginRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    PasswordLoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SendCodeRequest,
    SendCodeResponse,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services.auth.service import (
    authenticate_code_user,
    authenticate_password_user,
    create_password_reset_token,
    refresh_user_token,
    register_user,
    reset_password_with_token,
    revoke_refresh_token,
    send_verification_code,
)


router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return register_user(db, payload)


@router.post("/login/password", response_model=TokenResponse)
def password_login(
    payload: PasswordLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return authenticate_password_user(db, payload)


@router.post("/login/code", response_model=TokenResponse)
def code_login(payload: CodeLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return authenticate_code_user(db, payload)


@router.post("/code/send", response_model=SendCodeResponse)
def send_code(payload: SendCodeRequest, db: Session = Depends(get_db)) -> SendCodeResponse:
    record = send_verification_code(db, payload.target, payload.channel, payload.purpose)
    debug_code = record.code if settings.app_env.lower() in {"development", "local"} else None
    return SendCodeResponse(
        message="Verification code created successfully",
        expires_at=record.expires_at,
        debug_code=debug_code,
    )


@router.post("/password/forgot", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
) -> ForgotPasswordResponse:
    token = create_password_reset_token(db, payload)
    return ForgotPasswordResponse(
        message="If the account exists, a reset token has been created.",
        reset_token=token if settings.app_env.lower() in {"development", "local"} else None,
    )


@router.post("/password/reset", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    reset_password_with_token(db, payload)
    return MessageResponse(message="Password has been reset successfully")


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return refresh_user_token(db, payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    revoke_refresh_token(db, payload.refresh_token, current_user.id)
    return MessageResponse(message="Logged out successfully")
