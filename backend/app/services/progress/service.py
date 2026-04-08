from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chat import ChatSession
from app.models.note import Note, Notebook
from app.models.planner import GoalStatus, StudyGoal, StudyTask, TaskStatus
from app.models.progress import KnowledgeMastery, LearningRecord, ReviewSchedule, ReviewStatus
from app.models.user import User
from app.schemas.progress import (
    KnowledgeMasteryUpsertRequest,
    LearningRecordCreateRequest,
    ReviewScheduleCreateRequest,
    ReviewScheduleUpdateRequest,
)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def list_learning_records(
    db: Session,
    user: User,
    *,
    subject: str | None = None,
    limit: int = 20,
) -> list[LearningRecord]:
    statement = select(LearningRecord).where(LearningRecord.user_id == user.id)
    if subject:
        statement = statement.where(LearningRecord.subject == subject.strip())
    statement = statement.order_by(LearningRecord.created_at.desc()).limit(limit)
    return list(db.scalars(statement).all())


def create_learning_record(
    db: Session,
    user: User,
    payload: LearningRecordCreateRequest,
) -> LearningRecord:
    record = LearningRecord(user_id=user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_mastery_items(
    db: Session,
    user: User,
    *,
    subject: str | None = None,
    limit: int = 100,
) -> list[KnowledgeMastery]:
    statement = select(KnowledgeMastery).where(KnowledgeMastery.user_id == user.id)
    if subject:
        statement = statement.where(KnowledgeMastery.subject == subject.strip())
    statement = statement.order_by(
        KnowledgeMastery.mastery_score.asc(),
        KnowledgeMastery.updated_at.desc(),
    ).limit(limit)
    return list(db.scalars(statement).all())


def upsert_mastery_item(
    db: Session,
    user: User,
    payload: KnowledgeMasteryUpsertRequest,
) -> KnowledgeMastery:
    normalized_subject = payload.subject.strip() if payload.subject else None
    item = db.scalar(
        select(KnowledgeMastery).where(
            KnowledgeMastery.user_id == user.id,
            KnowledgeMastery.knowledge_point == payload.knowledge_point.strip(),
            KnowledgeMastery.subject == normalized_subject,
        )
    )

    if item is None:
        item = KnowledgeMastery(
            user_id=user.id,
            knowledge_point=payload.knowledge_point.strip(),
            subject=normalized_subject,
            mastery_score=payload.mastery_score,
            accuracy_rate=payload.accuracy_rate,
            last_practiced_at=payload.last_practiced_at,
            next_review_at=payload.next_review_at,
        )
    else:
        item.mastery_score = payload.mastery_score
        item.accuracy_rate = payload.accuracy_rate
        item.last_practiced_at = payload.last_practiced_at
        item.next_review_at = payload.next_review_at

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_review_schedules(
    db: Session,
    user: User,
    *,
    status_filter: ReviewStatus | None = None,
    due_only: bool = False,
    limit: int = 20,
) -> list[ReviewSchedule]:
    today = date.today()
    statement = select(ReviewSchedule).where(ReviewSchedule.user_id == user.id)
    if status_filter is not None:
        statement = statement.where(ReviewSchedule.status == status_filter)
    if due_only:
        statement = statement.where(ReviewSchedule.scheduled_for <= today)
    statement = statement.order_by(ReviewSchedule.scheduled_for.asc(), ReviewSchedule.created_at.asc()).limit(limit)
    return list(db.scalars(statement).all())


def create_review_schedule(
    db: Session,
    user: User,
    payload: ReviewScheduleCreateRequest,
) -> ReviewSchedule:
    review = ReviewSchedule(user_id=user.id, **payload.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_review_schedule_or_404(db: Session, user: User, review_id: UUID) -> ReviewSchedule:
    review = db.scalar(
        select(ReviewSchedule).where(
            ReviewSchedule.id == review_id,
            ReviewSchedule.user_id == user.id,
        )
    )
    if review is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review schedule not found")
    return review


def update_review_schedule(
    db: Session,
    review: ReviewSchedule,
    payload: ReviewScheduleUpdateRequest,
) -> ReviewSchedule:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(review, field, value)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def build_progress_overview(db: Session, user: User) -> dict[str, Any]:
    today = date.today()

    total_goals = int(db.scalar(select(func.count(StudyGoal.id)).where(StudyGoal.user_id == user.id)) or 0)
    active_goals = int(
        db.scalar(
            select(func.count(StudyGoal.id)).where(
                StudyGoal.user_id == user.id,
                StudyGoal.status == GoalStatus.active,
            )
        )
        or 0
    )
    completed_goals = int(
        db.scalar(
            select(func.count(StudyGoal.id)).where(
                StudyGoal.user_id == user.id,
                StudyGoal.status == GoalStatus.completed,
            )
        )
        or 0
    )
    total_tasks = int(db.scalar(select(func.count(StudyTask.id)).where(StudyTask.user_id == user.id)) or 0)
    completed_tasks = int(
        db.scalar(
            select(func.count(StudyTask.id)).where(
                StudyTask.user_id == user.id,
                StudyTask.status == TaskStatus.completed,
            )
        )
        or 0
    )
    pending_tasks = int(
        db.scalar(
            select(func.count(StudyTask.id)).where(
                StudyTask.user_id == user.id,
                StudyTask.status == TaskStatus.pending,
            )
        )
        or 0
    )
    total_notes = int(db.scalar(select(func.count(Note.id)).where(Note.user_id == user.id)) or 0)
    total_notebooks = int(db.scalar(select(func.count(Notebook.id)).where(Notebook.user_id == user.id)) or 0)
    total_chat_sessions = int(
        db.scalar(select(func.count(ChatSession.id)).where(ChatSession.user_id == user.id)) or 0
    )
    total_learning_records = int(
        db.scalar(select(func.count(LearningRecord.id)).where(LearningRecord.user_id == user.id)) or 0
    )
    total_study_minutes = int(
        db.scalar(
            select(func.coalesce(func.sum(LearningRecord.duration_minutes), 0)).where(
                LearningRecord.user_id == user.id
            )
        )
        or 0
    )
    average_mastery_score = _to_float(
        db.scalar(select(func.avg(KnowledgeMastery.mastery_score)).where(KnowledgeMastery.user_id == user.id))
    )
    due_review_count = int(
        db.scalar(
            select(func.count(ReviewSchedule.id)).where(
                ReviewSchedule.user_id == user.id,
                ReviewSchedule.status == ReviewStatus.pending,
                ReviewSchedule.scheduled_for <= today,
            )
        )
        or 0
    )

    subject_rows = db.execute(
        select(
            LearningRecord.subject,
            func.count(LearningRecord.id),
            func.coalesce(func.sum(LearningRecord.duration_minutes), 0),
            func.avg(LearningRecord.score),
        )
        .where(
            LearningRecord.user_id == user.id,
            LearningRecord.subject.is_not(None),
        )
        .group_by(LearningRecord.subject)
        .order_by(
            func.coalesce(func.sum(LearningRecord.duration_minutes), 0).desc(),
            func.count(LearningRecord.id).desc(),
        )
    ).all()

    subject_breakdown = [
        {
            "subject": subject,
            "record_count": int(record_count or 0),
            "total_minutes": int(total_minutes or 0),
            "average_score": _to_float(avg_score),
        }
        for subject, record_count, total_minutes, avg_score in subject_rows
        if subject
    ]

    recent_records = list_learning_records(db, user, limit=10)
    upcoming_reviews = list(
        db.scalars(
            select(ReviewSchedule)
            .where(
                ReviewSchedule.user_id == user.id,
                ReviewSchedule.status == ReviewStatus.pending,
                ReviewSchedule.scheduled_for >= today,
            )
            .order_by(ReviewSchedule.scheduled_for.asc(), ReviewSchedule.created_at.asc())
            .limit(5)
        ).all()
    )

    return {
        "stats": {
            "total_goals": total_goals,
            "active_goals": active_goals,
            "completed_goals": completed_goals,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "total_notes": total_notes,
            "total_notebooks": total_notebooks,
            "total_chat_sessions": total_chat_sessions,
            "total_learning_records": total_learning_records,
            "total_study_minutes": total_study_minutes,
            "average_mastery_score": average_mastery_score,
            "due_review_count": due_review_count,
        },
        "subject_breakdown": subject_breakdown,
        "recent_records": recent_records,
        "upcoming_reviews": upcoming_reviews,
    }
