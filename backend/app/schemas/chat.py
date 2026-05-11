from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.chat import ChatSessionStatus, FeedbackValue, MessageRole


class ChatSessionCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    subject: str | None = Field(default=None, max_length=64)
    first_message: str | None = Field(default=None, min_length=1, max_length=4000)


class ChatSessionUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    subject: str | None = Field(default=None, max_length=64)
    status: ChatSessionStatus | None = None


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None = None
    subject: str | None = None
    status: ChatSessionStatus
    created_at: datetime
    updated_at: datetime


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    citations_json: list | None = None
    tokens_prompt: int | None = None
    tokens_completion: int | None = None
    model_name: str | None = None
    created_at: datetime
    updated_at: datetime


class ChatExchangeResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class ChatFeedbackRequest(BaseModel):
    value: FeedbackValue
    reason: str | None = None


class ChatFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    message_id: UUID
    value: FeedbackValue
    reason: str | None = None
    created_at: datetime
    updated_at: datetime
