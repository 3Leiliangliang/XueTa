from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.translate import (
    TranslatePolishRequest,
    TranslatePolishResponse,
    TranslateTextRequest,
    TranslateTextResponse,
)
from app.services.translate.service import polish_translation, translate_text


router = APIRouter()


@router.post('/text', response_model=TranslateTextResponse)
def translate_text_endpoint(
    payload: TranslateTextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TranslateTextResponse:
    result = translate_text(db, current_user, payload)
    return TranslateTextResponse.model_validate(result)


@router.post('/polish', response_model=TranslatePolishResponse)
def polish_text_endpoint(
    payload: TranslatePolishRequest,
    current_user: User = Depends(get_current_user),
) -> TranslatePolishResponse:
    _ = current_user
    result = polish_translation(payload)
    return TranslatePolishResponse.model_validate(result)
