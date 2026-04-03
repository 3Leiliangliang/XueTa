from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.planner import GoalStatus, StudyGoal, StudyPlanSnapshot, StudyTask, TaskSource
from app.models.user import User
from app.schemas.planner import (
    GoalCreateRequest,
    GoalUpdateRequest,
    PlannerGenerateRequest,
    TaskCreateRequest,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)


def list_goals(db: Session, user: User) -> list[StudyGoal]:
    statement = (
        select(StudyGoal)
        .where(StudyGoal.user_id == user.id)
        .order_by(StudyGoal.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_goal_or_404(db: Session, user: User, goal_id: UUID) -> StudyGoal:
    goal = db.scalar(
        select(StudyGoal).where(StudyGoal.id == goal_id, StudyGoal.user_id == user.id)
    )
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


def create_goal(db: Session, user: User, payload: GoalCreateRequest) -> StudyGoal:
    goal = StudyGoal(user_id=user.id, progress=0, status=GoalStatus.active, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, goal: StudyGoal, payload: GoalUpdateRequest) -> StudyGoal:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(goal, field, value)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, goal: StudyGoal) -> None:
    db.delete(goal)
    db.commit()


def list_tasks(db: Session, user: User, goal_id: UUID | None = None) -> list[StudyTask]:
    statement = select(StudyTask).where(StudyTask.user_id == user.id)
    if goal_id is not None:
        statement = statement.where(StudyTask.goal_id == goal_id)
    statement = statement.order_by(StudyTask.task_date.asc(), StudyTask.task_time.asc(), StudyTask.created_at.desc())
    return list(db.scalars(statement).all())


def get_task_or_404(db: Session, user: User, task_id: UUID) -> StudyTask:
    task = db.scalar(
        select(StudyTask).where(StudyTask.id == task_id, StudyTask.user_id == user.id)
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def create_task(db: Session, user: User, payload: TaskCreateRequest) -> StudyTask:
    if payload.goal_id is not None:
        get_goal_or_404(db, user, payload.goal_id)
    task = StudyTask(user_id=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, user: User, task: StudyTask, payload: TaskUpdateRequest) -> StudyTask:
    updates = payload.model_dump(exclude_unset=True)
    if "goal_id" in updates and updates["goal_id"] is not None:
        get_goal_or_404(db, user, updates["goal_id"])
    for field, value in updates.items():
        setattr(task, field, value)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task_status(db: Session, task: StudyTask, payload: TaskStatusUpdateRequest) -> StudyTask:
    task.status = payload.status
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: StudyTask) -> None:
    db.delete(task)
    db.commit()


def generate_plan_snapshot(db: Session, user: User, payload: PlannerGenerateRequest) -> StudyPlanSnapshot:
    goals_statement = select(StudyGoal).where(
        StudyGoal.user_id == user.id,
        StudyGoal.status == GoalStatus.active,
    )
    if payload.goal_ids:
        goals_statement = goals_statement.where(StudyGoal.id.in_(payload.goal_ids))

    goals = list(db.scalars(goals_statement).all())
    if not goals:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active goals available for plan generation")

    today = date.today()
    generated_days: list[dict] = []
    minutes_per_goal = max(payload.daily_minutes // max(len(goals), 1), 30)

    for offset in range(payload.days):
        current_day = today + timedelta(days=offset)
        tasks = []
        for index, goal in enumerate(goals, start=1):
            tasks.append(
                {
                    "goal_id": str(goal.id),
                    "goal_title": goal.title,
                    "title": f"{goal.title} - Session {offset + 1}",
                    "duration_minutes": minutes_per_goal,
                    "priority": "medium",
                    "source": TaskSource.ai.value,
                    "suggested_order": index,
                }
            )
        generated_days.append({"date": current_day.isoformat(), "tasks": tasks})

    snapshot = StudyPlanSnapshot(
        user_id=user.id,
        title=f"{payload.days}-day study plan",
        summary=f"Generated a {payload.days}-day study plan for {len(goals)} active goals.",
        plan_json={
            "days": generated_days,
            "daily_minutes": payload.daily_minutes,
            "goal_count": len(goals),
        },
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot
