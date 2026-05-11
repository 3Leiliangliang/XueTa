from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UserStatus(str, enum.Enum):
    active = "active"
    pending = "pending"
    disabled = "disabled"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name="user_status"), default=UserStatus.pending
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped[UserProfile | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    study_goals: Mapped[list["StudyGoal"]] = relationship(back_populates="user")
    study_tasks: Mapped[list["StudyTask"]] = relationship(back_populates="user")
    study_plan_snapshots: Mapped[list["StudyPlanSnapshot"]] = relationship(
        back_populates="user"
    )
    notebooks: Mapped[list["Notebook"]] = relationship(back_populates="user")
    notes: Mapped[list["Note"]] = relationship(back_populates="user")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")
    knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(back_populates="user")
    practice_sets: Mapped[list["PracticeSet"]] = relationship(back_populates="user")
    practice_attempts: Mapped[list["PracticeAttempt"]] = relationship(back_populates="user")
    learning_records: Mapped[list["LearningRecord"]] = relationship(back_populates="user")
    knowledge_mastery_items: Mapped[list["KnowledgeMastery"]] = relationship(
        back_populates="user"
    )
    review_schedules: Mapped[list["ReviewSchedule"]] = relationship(back_populates="user")
    desktop_layouts: Mapped[list["DesktopLayout"]] = relationship(back_populates="user")
    saved_items: Mapped[list["SavedItem"]] = relationship(back_populates="user")
    uploaded_files: Mapped[list["UploadedFile"]] = relationship(back_populates="user")
    verification_codes: Mapped[list["VerificationCode"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user"
    )


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    display_name: Mapped[str | None] = mapped_column(String(128))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    grade_level: Mapped[str | None] = mapped_column(String(64))
    target_exam: Mapped[str | None] = mapped_column(String(128))
    preferred_subjects: Mapped[str | None] = mapped_column(Text)
    learning_style: Mapped[str | None] = mapped_column(String(128))
    bio: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="profile")
