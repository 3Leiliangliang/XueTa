from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.practice import AttemptStatus, PracticeDifficulty, PracticeItemType

JsonValue = dict | list | str | int | float | bool | None


class PracticeGenerateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    subject: str | None = Field(default=None, max_length=64)
    knowledge_points: list[str] | None = None
    item_count: int = Field(default=5, ge=1, le=30)
    difficulty: PracticeDifficulty = PracticeDifficulty.medium
    item_types: list[PracticeItemType] | None = None


class PracticeItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: PracticeItemType
    stem: str
    options_json: list | None = None
    explanation: str | None = None
    difficulty: PracticeDifficulty
    knowledge_points_json: list | None = None
    created_at: datetime
    updated_at: datetime


class PracticeSetSummaryResponse(BaseModel):
    id: UUID
    title: str
    subject: str | None = None
    source: str
    config_json: dict | None = None
    item_count: int
    created_at: datetime
    updated_at: datetime


class PracticeSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    subject: str | None = None
    source: str
    config_json: dict | None = None
    items: list[PracticeItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PracticeAnswerSubmitItem(BaseModel):
    item_id: UUID
    answer_json: JsonValue = None


class PracticeAttemptSubmitRequest(BaseModel):
    answers: list[PracticeAnswerSubmitItem]
    duration_minutes: int | None = Field(default=None, ge=0, le=10080)


class PracticeAttemptAnswerResultResponse(BaseModel):
    item_id: UUID
    answer_json: JsonValue = None
    correct_answer_json: JsonValue = None
    is_correct: bool
    score: float
    feedback_text: str | None = None


class PracticeAttemptSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    set_id: UUID
    status: AttemptStatus
    score: float | None = None
    evaluation_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class PracticeAttemptResponse(BaseModel):
    id: UUID
    set_id: UUID
    status: AttemptStatus
    score: float | None = None
    evaluation_json: dict | None = None
    answers: list[PracticeAttemptAnswerResultResponse]
    created_at: datetime
    updated_at: datetime


class WrongQuestionResponse(BaseModel):
    id: UUID
    item_id: UUID
    practice_set_id: UUID
    stem: str
    wrong_count: int
    last_feedback: str | None = None
    knowledge_points_json: list | None = None
    created_at: datetime
    updated_at: datetime
