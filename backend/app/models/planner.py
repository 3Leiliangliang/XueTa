from __future__ import annotations

import enum
import uuid
from datetime import date, time

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GoalStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    archived = "archived"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    skipped = "skipped"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskSource(str, enum.Enum):
    manual = "manual"
    ai = "ai"


class StudyGoal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "study_goals"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(String(64), index=True)
    deadline: Mapped[date | None] = mapped_column(Date)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[GoalStatus] = mapped_column(SQLEnum(GoalStatus, name="goal_status"), default=GoalStatus.active)
    color: Mapped[str | None] = mapped_column(String(128))

    user: Mapped["User"] = relationship(back_populates="study_goals")
    tasks: Mapped[list["StudyTask"]] = relationship(back_populates="goal")


class StudyTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "study_tasks"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("study_goals.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    task_date: Mapped[date | None] = mapped_column(Date, index=True)
    task_time: Mapped[time | None] = mapped_column(Time)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    priority: Mapped[TaskPriority] = mapped_column(
        SQLEnum(TaskPriority, name="task_priority"), default=TaskPriority.medium
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, name="task_status"), default=TaskStatus.pending
    )
    source: Mapped[TaskSource] = mapped_column(
        SQLEnum(TaskSource, name="task_source"), default=TaskSource.manual
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="study_tasks")
    goal: Mapped[StudyGoal | None] = relationship(back_populates="tasks")


class StudyPlanSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "study_plan_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    plan_json: Mapped[dict] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="study_plan_snapshots")
