from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeBase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_bases"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(String(64), index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="knowledge_bases")
    documents: Mapped[list["KnowledgeDocument"]] = relationship(back_populates="knowledge_base")


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True)
    uploaded_file_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("uploaded_files.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    source_type: Mapped[str] = mapped_column(String(32), default="upload")
    source_url: Mapped[str | None] = mapped_column(String(512))
    mime_type: Mapped[str | None] = mapped_column(String(128))
    content_text: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    knowledge_base: Mapped[KnowledgeBase] = relationship(back_populates="documents")
    uploaded_file: Mapped["UploadedFile | None"] = relationship(back_populates="knowledge_documents")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="document")


class KnowledgeChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")
    embedding: Mapped["KnowledgeChunkEmbedding | None"] = relationship(
        back_populates="chunk", cascade="all, delete-orphan", uselist=False
    )


class KnowledgeChunkEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_chunk_embeddings"

    chunk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_chunks.id", ondelete="CASCADE"), unique=True, index=True)
    embedding_model: Mapped[str] = mapped_column(String(128))
    dimensions: Mapped[int] = mapped_column(Integer, default=1536)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536))

    chunk: Mapped[KnowledgeChunk] = relationship(back_populates="embedding")

