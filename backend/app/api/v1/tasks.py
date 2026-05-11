from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.schemas.tasks import TaskEnqueueRequest, TaskEnqueueResponse, TaskStatusResponse
from app.tasks.queue import enqueue_task, get_task_status
from app.tasks.registry import get_task
from app.tasks import demo  # noqa: F401

router = APIRouter()


@router.post("/enqueue", response_model=TaskEnqueueResponse, status_code=status.HTTP_202_ACCEPTED)
def enqueue_task_endpoint(
    payload: TaskEnqueueRequest,
    current_user=Depends(get_current_user),
):
    task_fn = get_task(payload.task_name)
    if task_fn is None:
        raise HTTPException(status_code=404, detail="Task not registered")
    task_id = enqueue_task(payload.task_name, payload.payload, user_id=str(current_user.id))
    return TaskEnqueueResponse(task_id=task_id, status="queued")


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status_endpoint(
    task_id: str,
    current_user=Depends(get_current_user),
):
    task_data = get_task_status(task_id)
    if task_data is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task_data.get("user_id") and task_data.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    return TaskStatusResponse(**task_data)

