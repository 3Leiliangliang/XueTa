from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.practice import (
    PracticeAttemptResponse,
    PracticeAttemptSubmitRequest,
    PracticeAttemptSummaryResponse,
    PracticeGenerateRequest,
    PracticeSetResponse,
    PracticeSetSummaryResponse,
    WrongQuestionResponse,
)
from app.services.practice.service import (
    generate_practice_set,
    get_attempt_response,
    get_practice_set_response,
    list_attempts_for_set,
    list_practice_sets,
    list_wrong_questions,
    submit_attempt,
)


router = APIRouter()


@router.post("/generate", response_model=PracticeSetResponse, status_code=status.HTTP_201_CREATED)
def generate_practice_endpoint(
    payload: PracticeGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PracticeSetResponse:
    practice_set = generate_practice_set(db, current_user, payload)
    return PracticeSetResponse.model_validate(practice_set)


@router.get("/sets", response_model=list[PracticeSetSummaryResponse])
def get_practice_sets(
    subject: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PracticeSetSummaryResponse]:
    practice_sets = list_practice_sets(db, current_user, subject)
    return [PracticeSetSummaryResponse.model_validate(item) for item in practice_sets]


@router.get("/sets/{set_id}", response_model=PracticeSetResponse)
def get_practice_set(
    set_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PracticeSetResponse:
    practice_set = get_practice_set_response(db, current_user, set_id)
    return PracticeSetResponse.model_validate(practice_set)


@router.get("/sets/{set_id}/attempts", response_model=list[PracticeAttemptSummaryResponse])
def get_practice_attempts(
    set_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PracticeAttemptSummaryResponse]:
    attempts = list_attempts_for_set(db, current_user, set_id)
    return [PracticeAttemptSummaryResponse.model_validate(attempt) for attempt in attempts]


@router.post("/sets/{set_id}/attempts", response_model=PracticeAttemptResponse, status_code=status.HTTP_201_CREATED)
def submit_practice_attempt(
    set_id: UUID,
    payload: PracticeAttemptSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PracticeAttemptResponse:
    attempt = submit_attempt(db, current_user, set_id, payload)
    return PracticeAttemptResponse.model_validate(attempt)


@router.get("/attempts/{attempt_id}", response_model=PracticeAttemptResponse)
def get_practice_attempt(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PracticeAttemptResponse:
    attempt = get_attempt_response(db, current_user, attempt_id)
    return PracticeAttemptResponse.model_validate(attempt)


@router.get("/wrong-questions", response_model=list[WrongQuestionResponse])
def get_wrong_questions(
    subject: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WrongQuestionResponse]:
    rows = list_wrong_questions(db, current_user, subject)
    return [WrongQuestionResponse.model_validate(row) for row in rows]
