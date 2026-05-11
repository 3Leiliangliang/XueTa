from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.progress import ReviewStatus
from app.models.user import User
from app.schemas.progress import (
    KnowledgeMasteryResponse,
    KnowledgeMasteryUpsertRequest,
    LearningRecordCreateRequest,
    LearningRecordResponse,
    ProgressOverviewResponse,
    ReviewScheduleCreateRequest,
    ReviewScheduleResponse,
    ReviewScheduleUpdateRequest,
)
from app.services.progress.service import (
    build_progress_overview,
    create_learning_record,
    create_review_schedule,
    get_review_schedule_or_404,
    list_learning_records,
    list_mastery_items,
    list_review_schedules,
    update_review_schedule,
    upsert_mastery_item,
)


router = APIRouter()


@router.get("/overview", response_model=ProgressOverviewResponse)
def progress_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProgressOverviewResponse:
    overview = build_progress_overview(db, current_user)
    return ProgressOverviewResponse.model_validate(overview)


@router.get("/mastery", response_model=list[KnowledgeMasteryResponse])
def mastery(
    subject: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeMasteryResponse]:
    items = list_mastery_items(db, current_user, subject=subject, limit=limit)
    return [KnowledgeMasteryResponse.model_validate(item) for item in items]


@router.post("/mastery", response_model=KnowledgeMasteryResponse)
def upsert_mastery(
    payload: KnowledgeMasteryUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeMasteryResponse:
    item = upsert_mastery_item(db, current_user, payload)
    return KnowledgeMasteryResponse.model_validate(item)


@router.get("/records", response_model=list[LearningRecordResponse])
def get_learning_records(
    subject: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LearningRecordResponse]:
    records = list_learning_records(db, current_user, subject=subject, limit=limit)
    return [LearningRecordResponse.model_validate(record) for record in records]


@router.post("/records", response_model=LearningRecordResponse, status_code=status.HTTP_201_CREATED)
def create_learning_record_endpoint(
    payload: LearningRecordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LearningRecordResponse:
    record = create_learning_record(db, current_user, payload)
    return LearningRecordResponse.model_validate(record)


@router.get("/reviews", response_model=list[ReviewScheduleResponse])
def get_review_schedules(
    status_filter: ReviewStatus | None = Query(default=None, alias="status"),
    due_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReviewScheduleResponse]:
    reviews = list_review_schedules(
        db,
        current_user,
        status_filter=status_filter,
        due_only=due_only,
        limit=limit,
    )
    return [ReviewScheduleResponse.model_validate(review) for review in reviews]


@router.post("/reviews", response_model=ReviewScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_review_schedule_endpoint(
    payload: ReviewScheduleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewScheduleResponse:
    review = create_review_schedule(db, current_user, payload)
    return ReviewScheduleResponse.model_validate(review)


@router.patch("/reviews/{review_id}", response_model=ReviewScheduleResponse)
def update_review_schedule_endpoint(
    review_id: UUID,
    payload: ReviewScheduleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewScheduleResponse:
    review = get_review_schedule_or_404(db, current_user, review_id)
    review = update_review_schedule(db, review, payload)
    return ReviewScheduleResponse.model_validate(review)
