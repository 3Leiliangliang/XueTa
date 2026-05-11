from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TaskEnqueueRequest(BaseModel):
    task_name: str
    payload: dict[str, Any] | None = None


class TaskEnqueueResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    task_name: str
    status: str
    payload: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    user_id: str | None = None
