from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.progress import LearningRecordType, ReviewStatus


class LearningRecordCreateRequest(BaseModel):
    record_type: LearningRecordType
    subject: str | None = Field(default=None, max_length=64)
    duration_minutes: int | None = Field(default=None, ge=0, le=10080)
    score: float | None = Field(default=None, ge=0, le=100)
    reference_type: str | None = Field(default=None, max_length=64)
    reference_id: UUID | None = None
    metadata_json: dict | None = None


class LearningRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    record_type: LearningRecordType
    subject: str | None = None
    duration_minutes: int | None = None
    score: float | None = None
    reference_type: str | None = None
    reference_id: UUID | None = None
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeMasteryUpsertRequest(BaseModel):
    knowledge_point: str = Field(min_length=1, max_length=255)
    subject: str | None = Field(default=None, max_length=64)
    mastery_score: float = Field(ge=0, le=100)
    accuracy_rate: float | None = Field(default=None, ge=0, le=100)
    last_practiced_at: date | None = None
    next_review_at: date | None = None


class KnowledgeMasteryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    knowledge_point: str
    subject: str | None = None
    mastery_score: float
    accuracy_rate: float | None = None
    last_practiced_at: date | None = None
    next_review_at: date | None = None
    created_at: datetime
    updated_at: datetime


class ReviewScheduleCreateRequest(BaseModel):
    knowledge_point: str = Field(min_length=1, max_length=255)
    subject: str | None = Field(default=None, max_length=64)
    scheduled_for: date
    status: ReviewStatus = ReviewStatus.pending
    review_payload: dict | None = None


class ReviewScheduleUpdateRequest(BaseModel):
    scheduled_for: date | None = None
    status: ReviewStatus | None = None
    review_payload: dict | None = None


class ReviewScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    knowledge_point: str
    subject: str | None = None
    scheduled_for: date
    status: ReviewStatus
    review_payload: dict | None = None
    created_at: datetime
    updated_at: datetime


class ProgressOverviewStatsResponse(BaseModel):
    total_goals: int
    active_goals: int
    completed_goals: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    total_notes: int
    total_notebooks: int
    total_chat_sessions: int
    total_learning_records: int
    total_study_minutes: int
    average_mastery_score: float | None = None
    due_review_count: int


class SubjectProgressResponse(BaseModel):
    subject: str
    record_count: int
    total_minutes: int
    average_score: float | None = None


class ProgressOverviewResponse(BaseModel):
    stats: ProgressOverviewStatsResponse
    subject_breakdown: list[SubjectProgressResponse]
    recent_records: list[LearningRecordResponse]
    upcoming_reviews: list[ReviewScheduleResponse]
