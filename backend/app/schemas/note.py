from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotebookCreateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    color: str | None = Field(default=None, max_length=128)


class NotebookUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    color: str | None = Field(default=None, max_length=128)


class NotebookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    color: str | None = None
    note_count: int
    created_at: datetime
    updated_at: datetime


class NoteCreateRequest(BaseModel):
    notebook_id: UUID | None = None
    title: str | None = Field(default=None, max_length=255)
    content_markdown: str = ""
    source_type: str = Field(default="manual", max_length=32)
    metadata_json: dict | None = None


class NoteUpdateRequest(BaseModel):
    notebook_id: UUID | None = None
    title: str | None = Field(default=None, max_length=255)
    content_markdown: str | None = None
    summary: str | None = None
    source_type: str | None = Field(default=None, max_length=32)
    metadata_json: dict | None = None


class NoteTodoCreateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=255)
    done: bool = False
    sort_order: int = Field(default=0, ge=0)


class NoteTodoUpdateRequest(BaseModel):
    text: str | None = Field(default=None, min_length=1, max_length=255)
    done: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)


class NoteTodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    note_id: UUID
    text: str
    done: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class NoteSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    note_id: UUID
    model_name: str | None = None
    summary_text: str
    suggestions_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    notebook_id: UUID | None = None
    title: str
    content_markdown: str
    summary: str | None = None
    source_type: str
    metadata_json: dict | None = None
    todos: list[NoteTodoResponse] = []
    summaries: list[NoteSummaryResponse] = []
    created_at: datetime
    updated_at: datetime
