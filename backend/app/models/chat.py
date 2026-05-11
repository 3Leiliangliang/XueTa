from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChatSessionStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


class MessageRole(str, enum.Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


class FeedbackValue(str, enum.Enum):
    up = "up"
    down = "down"


class ChatSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[ChatSessionStatus] = mapped_column(
        SQLEnum(ChatSessionStatus, name="chat_session_status"),
        default=ChatSessionStatus.active,
    )

    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="session")


class ChatMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[MessageRole] = mapped_column(SQLEnum(MessageRole, name="message_role"))
    content: Mapped[str] = mapped_column(Text)
    citations_json: Mapped[list | None] = mapped_column(JSONB)
    tokens_prompt: Mapped[int | None] = mapped_column(Integer)
    tokens_completion: Mapped[int | None] = mapped_column(Integer)
    model_name: Mapped[str | None] = mapped_column(String(128))

    session: Mapped[ChatSession] = relationship(back_populates="messages")
    feedback_items: Mapped[list["ChatFeedback"]] = relationship(back_populates="message")


class ChatFeedback(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "chat_feedback"

    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_messages.id", ondelete="CASCADE"), index=True)
    value: Mapped[FeedbackValue] = mapped_column(
        SQLEnum(FeedbackValue, name="chat_feedback_value")
    )
    reason: Mapped[str | None] = mapped_column(Text)

    message: Mapped[ChatMessage] = relationship(back_populates="feedback_items")
