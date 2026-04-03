from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.planner import (
    GoalCreateRequest,
    GoalResponse,
    GoalUpdateRequest,
    PlannerGenerateRequest,
    PlannerSnapshotResponse,
    TaskCreateRequest,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)
from app.services.planner.service import (
    create_goal,
    create_task,
    delete_goal,
    delete_task,
    generate_plan_snapshot,
    get_goal_or_404,
    get_task_or_404,
    list_goals,
    list_tasks,
    update_goal,
    update_task,
    update_task_status,
)


router = APIRouter()


@router.get("/goals", response_model=list[GoalResponse])
def get_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GoalResponse]:
    return [GoalResponse.model_validate(goal) for goal in list_goals(db, current_user)]


@router.post("/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal_endpoint(
    payload: GoalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalResponse:
    goal = create_goal(db, current_user, payload)
    return GoalResponse.model_validate(goal)


@router.get("/goals/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalResponse:
    goal = get_goal_or_404(db, current_user, goal_id)
    return GoalResponse.model_validate(goal)


@router.patch("/goals/{goal_id}", response_model=GoalResponse)
def update_goal_endpoint(
    goal_id: UUID,
    payload: GoalUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalResponse:
    goal = get_goal_or_404(db, current_user, goal_id)
    updated_goal = update_goal(db, goal, payload)
    return GoalResponse.model_validate(updated_goal)


@router.delete("/goals/{goal_id}", response_model=MessageResponse)
def delete_goal_endpoint(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    goal = get_goal_or_404(db, current_user, goal_id)
    delete_goal(db, goal)
    return MessageResponse(message="Goal deleted successfully")


@router.get("/tasks", response_model=list[TaskResponse])
def get_tasks(
    goal_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    return [TaskResponse.model_validate(task) for task in list_tasks(db, current_user, goal_id)]


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task_endpoint(
    payload: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = create_task(db, current_user, payload)
    return TaskResponse.model_validate(task)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = get_task_or_404(db, current_user, task_id)
    return TaskResponse.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task_endpoint(
    task_id: UUID,
    payload: TaskUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = get_task_or_404(db, current_user, task_id)
    updated_task = update_task(db, current_user, task, payload)
    return TaskResponse.model_validate(updated_task)


@router.patch("/tasks/{task_id}/status", response_model=TaskResponse)
def update_task_status_endpoint(
    task_id: UUID,
    payload: TaskStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = get_task_or_404(db, current_user, task_id)
    updated_task = update_task_status(db, task, payload)
    return TaskResponse.model_validate(updated_task)


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
def delete_task_endpoint(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    task = get_task_or_404(db, current_user, task_id)
    delete_task(db, task)
    return MessageResponse(message="Task deleted successfully")


@router.post("/generate", response_model=PlannerSnapshotResponse, status_code=status.HTTP_201_CREATED)
def generate_plan_endpoint(
    payload: PlannerGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlannerSnapshotResponse:
    snapshot = generate_plan_snapshot(db, current_user, payload)
    return PlannerSnapshotResponse.model_validate(snapshot)
