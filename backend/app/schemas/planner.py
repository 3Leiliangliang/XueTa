from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.planner import GoalStatus, TaskPriority, TaskSource, TaskStatus


class GoalCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    subject: str | None = Field(default=None, max_length=64)
    deadline: date | None = None
    color: str | None = Field(default=None, max_length=128)


class GoalUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    subject: str | None = Field(default=None, max_length=64)
    deadline: date | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    status: GoalStatus | None = None
    color: str | None = Field(default=None, max_length=128)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None = None
    subject: str | None = None
    deadline: date | None = None
    progress: int
    status: GoalStatus
    color: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskCreateRequest(BaseModel):
    goal_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    task_date: date | None = None
    task_time: time | None = None
    duration_minutes: int = Field(default=60, ge=1, le=1440)
    priority: TaskPriority = TaskPriority.medium
    source: TaskSource = TaskSource.manual
    metadata_json: dict | None = None


class TaskUpdateRequest(BaseModel):
    goal_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    task_date: date | None = None
    task_time: time | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    source: TaskSource | None = None
    metadata_json: dict | None = None


class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatus


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    goal_id: UUID | None = None
    title: str
    description: str | None = None
    task_date: date | None = None
    task_time: time | None = None
    duration_minutes: int
    priority: TaskPriority
    status: TaskStatus
    source: TaskSource
    metadata_json: dict | None = None
    created_at: datetime
    updated_at: datetime


class PlannerGenerateRequest(BaseModel):
    goal_ids: list[UUID] | None = None
    days: int = Field(default=7, ge=1, le=30)
    daily_minutes: int = Field(default=120, ge=30, le=720)


class PlannerSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    summary: str | None = None
    plan_json: dict
    created_at: datetime
    updated_at: datetime
