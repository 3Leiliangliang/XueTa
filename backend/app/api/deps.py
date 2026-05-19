from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.models.user import User, UserStatus
from app.core.database import get_db_session
from app.services.llm import LlmRequestConfig, reset_request_llm_config, set_request_llm_config


bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Session:
    yield from get_db_session()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
        )

    try:
        payload = decode_token(credentials.credentials)
        token_type = payload.get("type")
        subject = payload.get("sub")
        if token_type != "access" or not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
            )
        user_id = UUID(subject)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if user.status != UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not active",
        )
    return user


def _normalize_header_value(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def _header_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _parse_float_header(
    request: Request,
    name: str,
    *,
    minimum: float,
    maximum: float,
) -> float | None:
    value = _normalize_header_value(request.headers.get(name))
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if parsed < minimum or parsed > maximum:
        return None
    return parsed


def _parse_int_header(
    request: Request,
    name: str,
    *,
    minimum: int,
    maximum: int,
) -> int | None:
    value = _normalize_header_value(request.headers.get(name))
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    if parsed < minimum or parsed > maximum:
        return None
    return parsed


async def apply_request_llm_config(request: Request):
    if not _header_enabled(request.headers.get("x-xueta-llm-enabled")):
        yield
        return

    api_key = _normalize_header_value(request.headers.get("x-xueta-llm-api-key"))
    if api_key is None:
        yield
        return

    config = LlmRequestConfig(
        api_key=api_key,
        base_url=_normalize_header_value(request.headers.get("x-xueta-llm-base-url")),
        chat_model=_normalize_header_value(request.headers.get("x-xueta-llm-chat-model")) or "gpt-4o",
        embedding_model=(
            _normalize_header_value(request.headers.get("x-xueta-llm-embedding-model"))
            or "text-embedding-3-small"
        ),
        vision_model=_normalize_header_value(request.headers.get("x-xueta-llm-vision-model")),
        timeout_seconds=(
            _parse_float_header(
                request,
                "x-xueta-llm-timeout-seconds",
                minimum=5.0,
                maximum=120.0,
            )
            or 20.0
        ),
        temperature=_parse_float_header(
            request,
            "x-xueta-llm-temperature",
            minimum=0.0,
            maximum=2.0,
        ),
        max_tokens=_parse_int_header(
            request,
            "x-xueta-llm-max-tokens",
            minimum=128,
            maximum=8192,
        ),
        provider=_normalize_header_value(request.headers.get("x-xueta-llm-provider")) or "openai-compatible",
    )
    token = set_request_llm_config(config)
    try:
        yield
    finally:
        reset_request_llm_config(token)
