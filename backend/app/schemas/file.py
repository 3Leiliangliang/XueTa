from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UploadedFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    original_filename: str
    mime_type: str | None = None
    extension: str | None = None
    size_bytes: int | None = None
    storage_path: str
    checksum: str | None = None
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime
