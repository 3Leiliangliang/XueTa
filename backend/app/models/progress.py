from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LearningRecordType(str, enum.Enum):
    study = "study"
    practice = "practice"
    review = "review"
    chat = "chat"
    note = "note"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    skipped = "skipped"


class LearningRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_records"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    record_type: Mapped[LearningRecordType] = mapped_column(
        SQLEnum(LearningRecordType, name="learning_record_type")
    )
    subject: Mapped[str | None] = mapped_column(String(64), index=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    reference_type: Mapped[str | None] = mapped_column(String(64))
    reference_id: Mapped[uuid.UUID | None] = mapped_column(index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="learning_records")


class KnowledgeMastery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_mastery"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str | None] = mapped_column(String(64), index=True)
    mastery_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    accuracy_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    last_practiced_at: Mapped[date | None] = mapped_column(Date)
    next_review_at: Mapped[date | None] = mapped_column(Date)

    user: Mapped["User"] = relationship(back_populates="knowledge_mastery_items")


class ReviewSchedule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "review_schedules"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str | None] = mapped_column(String(64), index=True)
    scheduled_for: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus, name="review_status"), default=ReviewStatus.pending
    )
    review_payload: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="review_schedules")
