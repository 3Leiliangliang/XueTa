from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DesktopLayoutCreateRequest(BaseModel):
    name: str = Field(default="default", min_length=1, max_length=128)
    layout_json: dict


class DesktopLayoutUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    layout_json: dict | None = None


class DesktopLayoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    layout_json: dict
    created_at: datetime
    updated_at: datetime
