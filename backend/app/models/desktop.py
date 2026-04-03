from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DesktopLayout(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "desktop_layouts"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128), default="default")
    layout_json: Mapped[dict] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="desktop_layouts")


class SavedItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "saved_items"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    item_type: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str | None] = mapped_column(String(64))
    payload_json: Mapped[dict] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="saved_items")
