from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PracticeItemType(str, enum.Enum):
    single = "single"
    multiple = "multiple"
    fill = "fill"
    short = "short"
    code = "code"


class PracticeDifficulty(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class AttemptStatus(str, enum.Enum):
    submitted = "submitted"
    graded = "graded"


class PracticeSet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "practice_sets"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(32), default="ai")
    config_json: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="practice_sets")
    items: Mapped[list["PracticeItem"]] = relationship(back_populates="practice_set")
    attempts: Mapped[list["PracticeAttempt"]] = relationship(back_populates="practice_set")


class PracticeItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "practice_items"

    set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("practice_sets.id", ondelete="CASCADE"), index=True)
    type: Mapped[PracticeItemType] = mapped_column(
        SQLEnum(PracticeItemType, name="practice_item_type")
    )
    stem: Mapped[str] = mapped_column(Text)
    options_json: Mapped[list | None] = mapped_column(JSONB)
    answer_json: Mapped[dict | list | str | None] = mapped_column(JSONB)
    explanation: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[PracticeDifficulty] = mapped_column(
        SQLEnum(PracticeDifficulty, name="practice_difficulty"),
        default=PracticeDifficulty.medium,
    )
    knowledge_points_json: Mapped[list | None] = mapped_column(JSONB)

    practice_set: Mapped[PracticeSet] = relationship(back_populates="items")
    answers: Mapped[list["PracticeAnswer"]] = relationship(back_populates="practice_item")
    wrong_question_entries: Mapped[list["WrongQuestion"]] = relationship(back_populates="practice_item")


class PracticeAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "practice_attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("practice_sets.id", ondelete="CASCADE"), index=True)
    status: Mapped[AttemptStatus] = mapped_column(
        SQLEnum(AttemptStatus, name="practice_attempt_status"),
        default=AttemptStatus.submitted,
    )
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    evaluation_json: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="practice_attempts")
    practice_set: Mapped[PracticeSet] = relationship(back_populates="attempts")
    answers: Mapped[list["PracticeAnswer"]] = relationship(back_populates="attempt")


class PracticeAnswer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "practice_answers"

    attempt_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("practice_attempts.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("practice_items.id", ondelete="CASCADE"), index=True)
    answer_json: Mapped[dict | list | str | None] = mapped_column(JSONB)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    feedback_text: Mapped[str | None] = mapped_column(Text)

    attempt: Mapped[PracticeAttempt] = relationship(back_populates="answers")
    practice_item: Mapped[PracticeItem] = relationship(back_populates="answers")


class WrongQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "wrong_questions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("practice_items.id", ondelete="CASCADE"), index=True)
    answer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("practice_answers.id", ondelete="SET NULL"), index=True)
    wrong_count: Mapped[int] = mapped_column(Integer, default=1)
    last_feedback: Mapped[str | None] = mapped_column(Text)

    practice_item: Mapped[PracticeItem] = relationship(back_populates="wrong_question_entries")
