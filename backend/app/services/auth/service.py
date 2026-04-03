from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.auth import PasswordResetToken, RefreshToken, VerificationChannel, VerificationCode
from app.models.user import User, UserProfile, UserStatus
from app.schemas.auth import (
    CodeLoginRequest,
    ForgotPasswordRequest,
    PasswordLoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse


def _normalize_identifier(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _find_user_by_identifier(db: Session, identifier: str) -> User | None:
    normalized = identifier.strip()
    return db.scalar(
        select(User).where(
            or_(
                User.email == normalized,
                User.username == normalized,
                User.phone == normalized,
            )
        )
    )


def _ensure_unique_user_fields(
    db: Session,
    *,
    username: str,
    email: str | None,
    phone: str | None,
) -> None:
    conditions = [User.username == username]
    if email:
        conditions.append(User.email == email)
    if phone:
        conditions.append(User.phone == phone)

    existing_user = db.scalar(select(User).where(or_(*conditions)))
    if existing_user is None:
        return

    if existing_user.username == username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    if email and existing_user.email == email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    if phone and existing_user.phone == phone:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone already exists")


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    refresh_expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    db.add(
        RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=refresh_expires_at,
        )
    )
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


def register_user(db: Session, payload: RegisterRequest) -> TokenResponse:
    email = _normalize_identifier(payload.email)
    phone = _normalize_identifier(payload.phone)
    username = payload.username.strip()

    _ensure_unique_user_fields(db, username=username, email=email, phone=phone)

    user = User(
        username=username,
        email=email,
        phone=phone,
        password_hash=hash_password(payload.password),
        status=UserStatus.active,
        email_verified=False,
        phone_verified=False,
    )
    profile = UserProfile(user=user, display_name=username)
    db.add_all([user, profile])
    db.commit()
    db.refresh(user)

    return _issue_tokens(db, user)


def authenticate_password_user(db: Session, payload: PasswordLoginRequest) -> TokenResponse:
    user = _find_user_by_identifier(db, payload.identifier)
    if user is None or not user.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    user.last_login_at = datetime.now(UTC)
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(db, user)


def send_verification_code(db: Session, target: str, channel: str, purpose: str) -> VerificationCode:
    normalized_target = target.strip()
    if channel not in {"sms", "email"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported verification channel")

    verification_code = f"{secrets.randbelow(1000000):06d}"
    expires_at = datetime.now(UTC) + timedelta(minutes=10)
    user = _find_user_by_identifier(db, normalized_target)

    record = VerificationCode(
        user_id=user.id if user else None,
        channel=VerificationChannel.sms if channel == "sms" else VerificationChannel.email,
        target=normalized_target,
        code=verification_code,
        purpose=purpose,
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def authenticate_code_user(db: Session, payload: CodeLoginRequest) -> TokenResponse:
    normalized_target = payload.target.strip()
    expected_channel = VerificationChannel.sms if payload.channel == "sms" else VerificationChannel.email
    record = db.scalar(
        select(VerificationCode)
        .where(
            VerificationCode.target == normalized_target,
            VerificationCode.code == payload.code,
            VerificationCode.channel == expected_channel,
            VerificationCode.purpose == "login",
            VerificationCode.consumed_at.is_(None),
        )
        .order_by(VerificationCode.created_at.desc())
    )
    if record is None or record.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired verification code")

    user = _find_user_by_identifier(db, normalized_target)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    record.consumed_at = datetime.now(UTC)
    user.last_login_at = datetime.now(UTC)
    if payload.channel == "sms":
        user.phone_verified = True
    else:
        user.email_verified = True
    db.add_all([record, user])
    db.commit()
    db.refresh(user)
    return _issue_tokens(db, user)


def refresh_user_token(db: Session, refresh_token: str) -> TokenResponse:
    token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked_at.is_(None),
        )
    )
    if token_record is None or token_record.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user_id = UUID(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from None

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if user.status != UserStatus.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    token_record.revoked_at = datetime.now(UTC)
    db.add(token_record)
    db.commit()
    return _issue_tokens(db, user)


def revoke_refresh_token(db: Session, refresh_token: str, current_user_id: UUID | None = None) -> None:
    token_record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token,
            RefreshToken.revoked_at.is_(None),
        )
    )
    if token_record is None:
        return
    if current_user_id is not None and token_record.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Refresh token does not belong to current user")

    token_record.revoked_at = datetime.now(UTC)
    db.add(token_record)
    db.commit()


def create_password_reset_token(db: Session, payload: ForgotPasswordRequest) -> str | None:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        return None

    token = secrets.token_urlsafe(32)
    record = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    db.add(record)
    db.commit()
    return token


def reset_password_with_token(db: Session, payload: ResetPasswordRequest) -> None:
    record = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token == payload.token,
            PasswordResetToken.used_at.is_(None),
        )
    )
    if record is None or record.expires_at < datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user = db.scalar(select(User).where(User.id == record.user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(payload.password)
    record.used_at = datetime.now(UTC)
    db.add_all([user, record])
    db.commit()
