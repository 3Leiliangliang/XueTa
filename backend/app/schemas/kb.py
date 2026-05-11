from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    subject: str | None = Field(default=None, max_length=64)
    is_public: bool = False


class KnowledgeBaseUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    subject: str | None = Field(default=None, max_length=64)
    is_public: bool | None = None


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    subject: str | None = None
    is_public: bool
    document_count: int
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentCreateRequest(BaseModel):
    knowledge_base_id: UUID
    uploaded_file_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    source_type: str = Field(default="manual", max_length=32)
    source_url: str | None = Field(default=None, max_length=512)
    mime_type: str | None = Field(default=None, max_length=128)
    content_text: str | None = None
    tags: list[str] | None = None
    metadata_json: dict | None = None


class KnowledgeDocumentUpdateRequest(BaseModel):
    knowledge_base_id: UUID | None = None
    uploaded_file_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    source_type: str | None = Field(default=None, max_length=32)
    source_url: str | None = Field(default=None, max_length=512)
    mime_type: str | None = Field(default=None, max_length=128)
    content_text: str | None = None
    tags: list[str] | None = None
    metadata_json: dict | None = None


class KnowledgeDocumentResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    uploaded_file_id: UUID | None = None
    title: str
    source_type: str
    source_url: str | None = None
    mime_type: str | None = None
    content_text: str | None = None
    tags: list[str] | None = None
    metadata_json: dict | None = None
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class KnowledgeChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeRetrieveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    knowledge_base_id: UUID | None = None
    subject: str | None = Field(default=None, max_length=64)
    limit: int = Field(default=5, ge=1, le=50)


class KnowledgeRetrieveHitResponse(BaseModel):
    knowledge_base_id: UUID
    document_id: UUID
    document_title: str
    chunk_id: UUID
    chunk_index: int
    content: str
    source_type: str
    score: float
    tags: list[str] | None = None


class KnowledgeRetrieveResponse(BaseModel):
    query: str
    total_hits: int
    hits: list[KnowledgeRetrieveHitResponse]
