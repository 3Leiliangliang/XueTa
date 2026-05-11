from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Notebook(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notebooks"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    color: Mapped[str | None] = mapped_column(String(128))
    note_count: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship(back_populates="notebooks")
    notes: Mapped[list["Note"]] = relationship(back_populates="notebook")


class Note(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notes"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    notebook_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("notebooks.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    content_markdown: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(32), default="manual")
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="notes")
    notebook: Mapped[Notebook | None] = relationship(back_populates="notes")
    todos: Mapped[list["NoteTodo"]] = relationship(back_populates="note")
    summaries: Mapped[list["NoteSummary"]] = relationship(back_populates="note")


class NoteTodo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "note_todos"

    note_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(255))
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    note: Mapped[Note] = relationship(back_populates="todos")


class NoteSummary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "note_summaries"

    note_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notes.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str | None] = mapped_column(String(128))
    summary_text: Mapped[str] = mapped_column(Text)
    suggestions_json: Mapped[dict | None] = mapped_column(JSONB)

    note: Mapped[Note] = relationship(back_populates="summaries")
