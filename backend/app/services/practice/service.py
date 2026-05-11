from __future__ import annotations

from datetime import date, timedelta
import math
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.practice import (
    AttemptStatus,
    PracticeAnswer,
    PracticeAttempt,
    PracticeDifficulty,
    PracticeItem,
    PracticeItemType,
    PracticeSet,
    WrongQuestion,
)
from app.models.progress import KnowledgeMastery, LearningRecord, LearningRecordType
from app.models.user import User
from app.schemas.practice import PracticeAttemptSubmitRequest, PracticeGenerateRequest

JsonValue = dict | list | str | int | float | bool | None


DEFAULT_ITEM_TYPES = [
    PracticeItemType.single,
    PracticeItemType.fill,
    PracticeItemType.short,
    PracticeItemType.multiple,
]


def _normalize_scalar(value: JsonValue) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().lower()


def _normalize_list(value: JsonValue) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        source = value
    else:
        source = [value]
    normalized = {_normalize_scalar(item) for item in source if _normalize_scalar(item)}
    return sorted(normalized)


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def _rotate_options(options: list[str], index: int) -> list[str]:
    if not options:
        return options
    offset = index % len(options)
    return options[offset:] + options[:offset]


def _build_generated_item(
    subject: str,
    knowledge_point: str,
    item_type: PracticeItemType,
    difficulty: PracticeDifficulty,
    index: int,
) -> dict[str, Any]:
    label = knowledge_point or f"{subject}核心概念{index + 1}"

    if item_type == PracticeItemType.single:
        correct = f"先理解{label}的定义与适用条件"
        options = _rotate_options(
            [
                correct,
                f"只记{label}结论，不看前提",
                f"遇到{label}题目时直接套模板",
                f"忽略{label}相关限制条件",
            ],
            index,
        )
        return {
            "type": item_type,
            "stem": f"关于“{label}”，以下哪项最能帮助你正确解题？",
            "options_json": options,
            "answer_json": correct,
            "explanation": f"处理{label}时，先把定义、条件和适用范围弄清楚通常最稳妥。",
            "difficulty": difficulty,
            "knowledge_points_json": [label],
        }

    if item_type == PracticeItemType.multiple:
        correct_answers = [f"梳理{label}的关键条件", f"通过例题验证{label}"]
        options = _rotate_options(
            correct_answers
            + [
                f"完全跳过{label}的定义",
                f"看到{label}就直接猜答案",
            ],
            index,
        )
        return {
            "type": item_type,
            "stem": f"学习“{label}”时，哪些做法更合理？",
            "options_json": options,
            "answer_json": correct_answers,
            "explanation": f"{label}通常需要同时理解条件与应用场景，只靠结论不够。",
            "difficulty": difficulty,
            "knowledge_points_json": [label],
        }

    if item_type == PracticeItemType.code:
        keywords = [label, "边界条件", "测试"]
        return {
            "type": item_type,
            "stem": f"请编写或描述一个小程序，用来验证“{label}”相关思路，并说明要关注哪些边界条件。",
            "options_json": None,
            "answer_json": {"keywords": keywords},
            "explanation": f"代码题重点不只在实现，还在于是否考虑{label}的输入边界与测试覆盖。",
            "difficulty": difficulty,
            "knowledge_points_json": [label],
        }

    if item_type == PracticeItemType.short:
        keywords = [label, "定义", "条件", "步骤"]
        return {
            "type": item_type,
            "stem": f"请简要说明“{label}”为什么容易出错，以及复习时应该重点检查什么。",
            "options_json": None,
            "answer_json": keywords,
            "explanation": f"简答题建议围绕概念定义、适用条件和解题步骤来组织答案。",
            "difficulty": difficulty,
            "knowledge_points_json": [label],
        }

    return {
        "type": PracticeItemType.fill,
        "stem": f"请填空：复习“{label}”时，第一步应先回到其____和适用条件。",
        "options_json": None,
        "answer_json": "定义",
        "explanation": f"无论是记忆型还是理解型知识点，定义都是最稳的起点。",
        "difficulty": difficulty,
        "knowledge_points_json": [label],
    }


def _evaluate_answer(item: PracticeItem, submitted_answer: JsonValue) -> tuple[bool, str]:
    expected = item.answer_json

    if item.type in {PracticeItemType.single, PracticeItemType.fill}:
        is_correct = _normalize_scalar(expected) == _normalize_scalar(submitted_answer)
    elif item.type == PracticeItemType.multiple:
        is_correct = _normalize_list(expected) == _normalize_list(submitted_answer)
    elif item.type == PracticeItemType.short:
        keywords = expected if isinstance(expected, list) else [expected]
        submitted = _normalize_scalar(submitted_answer)
        matches = sum(1 for keyword in keywords if _normalize_scalar(keyword) in submitted)
        is_correct = matches >= max(1, math.ceil(len(keywords) / 2))
    elif item.type == PracticeItemType.code:
        if isinstance(expected, dict):
            keywords = expected.get("keywords", [])
        elif isinstance(expected, list):
            keywords = expected
        else:
            keywords = [expected]
        submitted = _normalize_scalar(submitted_answer)
        matches = sum(1 for keyword in keywords if _normalize_scalar(keyword) in submitted)
        is_correct = matches >= max(1, math.ceil(len(keywords) / 2))
    else:
        is_correct = False

    if is_correct:
        return True, "回答正确，继续保持这个分析节奏。"

    return False, item.explanation or "这道题建议回到核心定义、条件和典型例题再复盘一次。"


def _update_wrong_question(
    db: Session,
    user: User,
    item: PracticeItem,
    answer_record: PracticeAnswer,
    feedback_text: str,
) -> None:
    wrong_entry = db.scalar(
        select(WrongQuestion).where(
            WrongQuestion.user_id == user.id,
            WrongQuestion.item_id == item.id,
        )
    )
    if wrong_entry is None:
        wrong_entry = WrongQuestion(
            user_id=user.id,
            item_id=item.id,
            answer_id=answer_record.id,
            wrong_count=1,
            last_feedback=feedback_text,
        )
    else:
        wrong_entry.answer_id = answer_record.id
        wrong_entry.wrong_count += 1
        wrong_entry.last_feedback = feedback_text
    db.add(wrong_entry)


def _record_progress(
    db: Session,
    user: User,
    practice_set: PracticeSet,
    attempt: PracticeAttempt,
    total_items: int,
    correct_count: int,
    duration_minutes: int | None,
    item_results: list[tuple[PracticeItem, bool]],
) -> None:
    record = LearningRecord(
        user_id=user.id,
        record_type=LearningRecordType.practice,
        subject=practice_set.subject,
        duration_minutes=duration_minutes,
        score=float(attempt.score or 0),
        reference_type="practice_set",
        reference_id=practice_set.id,
        metadata_json={
            "attempt_id": str(attempt.id),
            "correct_count": correct_count,
            "total_items": total_items,
        },
    )
    db.add(record)

    today = date.today()
    grouped: dict[str, dict[str, int]] = {}
    for item, is_correct in item_results:
        for knowledge_point in item.knowledge_points_json or []:
            stats = grouped.setdefault(knowledge_point, {"total": 0, "correct": 0})
            stats["total"] += 1
            if is_correct:
                stats["correct"] += 1

    for knowledge_point, stats in grouped.items():
        accuracy_rate = round((stats["correct"] / max(stats["total"], 1)) * 100, 2)
        mastery = db.scalar(
            select(KnowledgeMastery).where(
                KnowledgeMastery.user_id == user.id,
                KnowledgeMastery.knowledge_point == knowledge_point,
                KnowledgeMastery.subject == practice_set.subject,
            )
        )
        if mastery is None:
            mastery = KnowledgeMastery(
                user_id=user.id,
                knowledge_point=knowledge_point,
                subject=practice_set.subject,
                mastery_score=accuracy_rate,
                accuracy_rate=accuracy_rate,
                last_practiced_at=today,
                next_review_at=today + timedelta(days=7 if accuracy_rate >= 80 else 3 if accuracy_rate >= 50 else 1),
            )
        else:
            base_score = float(mastery.mastery_score or 0)
            mastery.mastery_score = _clamp_score(base_score * 0.65 + accuracy_rate * 0.35)
            mastery.accuracy_rate = accuracy_rate
            mastery.last_practiced_at = today
            mastery.next_review_at = today + timedelta(days=7 if accuracy_rate >= 80 else 3 if accuracy_rate >= 50 else 1)
        db.add(mastery)


def _list_items_for_set(db: Session, practice_set: PracticeSet) -> list[PracticeItem]:
    return list(
        db.scalars(
            select(PracticeItem)
            .where(PracticeItem.set_id == practice_set.id)
            .order_by(PracticeItem.created_at.asc())
        ).all()
    )


def _serialize_set(practice_set: PracticeSet, items: list[PracticeItem]) -> dict[str, Any]:
    return {
        "id": practice_set.id,
        "title": practice_set.title,
        "subject": practice_set.subject,
        "source": practice_set.source,
        "config_json": practice_set.config_json,
        "items": items,
        "created_at": practice_set.created_at,
        "updated_at": practice_set.updated_at,
    }


def _serialize_attempt(
    attempt: PracticeAttempt,
    answer_rows: list[PracticeAnswer],
    items_by_id: dict[UUID, PracticeItem],
) -> dict[str, Any]:
    return {
        "id": attempt.id,
        "set_id": attempt.set_id,
        "status": attempt.status,
        "score": float(attempt.score) if attempt.score is not None else None,
        "evaluation_json": attempt.evaluation_json,
        "answers": [
            {
                "item_id": answer.item_id,
                "answer_json": answer.answer_json,
                "correct_answer_json": items_by_id[answer.item_id].answer_json if answer.item_id in items_by_id else None,
                "is_correct": bool(answer.is_correct),
                "score": float(answer.score) if answer.score is not None else 0.0,
                "feedback_text": answer.feedback_text,
            }
            for answer in answer_rows
        ],
        "created_at": attempt.created_at,
        "updated_at": attempt.updated_at,
    }


def list_practice_sets(
    db: Session,
    user: User,
    subject: str | None = None,
) -> list[dict[str, Any]]:
    statement = (
        select(PracticeSet, func.count(PracticeItem.id))
        .outerjoin(PracticeItem, PracticeItem.set_id == PracticeSet.id)
        .where(PracticeSet.user_id == user.id)
        .group_by(PracticeSet.id)
        .order_by(PracticeSet.created_at.desc())
    )
    if subject:
        statement = statement.where(PracticeSet.subject == subject.strip())

    rows = db.execute(statement).all()
    return [
        {
            "id": practice_set.id,
            "title": practice_set.title,
            "subject": practice_set.subject,
            "source": practice_set.source,
            "config_json": practice_set.config_json,
            "item_count": int(item_count or 0),
            "created_at": practice_set.created_at,
            "updated_at": practice_set.updated_at,
        }
        for practice_set, item_count in rows
    ]


def get_practice_set_or_404(db: Session, user: User, set_id: UUID) -> PracticeSet:
    practice_set = db.scalar(
        select(PracticeSet).where(
            PracticeSet.id == set_id,
            PracticeSet.user_id == user.id,
        )
    )
    if practice_set is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice set not found")
    return practice_set


def get_practice_set_response(db: Session, user: User, set_id: UUID) -> dict[str, Any]:
    practice_set = get_practice_set_or_404(db, user, set_id)
    items = _list_items_for_set(db, practice_set)
    return _serialize_set(practice_set, items)


def generate_practice_set(db: Session, user: User, payload: PracticeGenerateRequest) -> dict[str, Any]:
    subject = (payload.subject or "通用练习").strip()
    knowledge_points = [point.strip() for point in (payload.knowledge_points or []) if point.strip()]
    if not knowledge_points:
        knowledge_points = [f"{subject}核心概念"]

    item_types = payload.item_types or DEFAULT_ITEM_TYPES
    title = payload.title.strip() if payload.title else f"{subject}练习集"

    practice_set = PracticeSet(
        user_id=user.id,
        title=title,
        subject=subject,
        source="rule-based",
        config_json={
            "knowledge_points": knowledge_points,
            "item_count": payload.item_count,
            "difficulty": payload.difficulty.value,
            "item_types": [item_type.value for item_type in item_types],
        },
    )
    db.add(practice_set)
    db.flush()

    items: list[PracticeItem] = []
    for index in range(payload.item_count):
        item_type = item_types[index % len(item_types)]
        knowledge_point = knowledge_points[index % len(knowledge_points)]
        item_payload = _build_generated_item(subject, knowledge_point, item_type, payload.difficulty, index)
        item = PracticeItem(set_id=practice_set.id, **item_payload)
        db.add(item)
        items.append(item)

    db.commit()
    db.refresh(practice_set)
    for item in items:
        db.refresh(item)

    return _serialize_set(practice_set, items)


def list_attempts_for_set(db: Session, user: User, set_id: UUID) -> list[PracticeAttempt]:
    get_practice_set_or_404(db, user, set_id)
    return list(
        db.scalars(
            select(PracticeAttempt)
            .where(
                PracticeAttempt.user_id == user.id,
                PracticeAttempt.set_id == set_id,
            )
            .order_by(PracticeAttempt.created_at.desc())
        ).all()
    )


def get_attempt_or_404(db: Session, user: User, attempt_id: UUID) -> PracticeAttempt:
    attempt = db.scalar(
        select(PracticeAttempt).where(
            PracticeAttempt.id == attempt_id,
            PracticeAttempt.user_id == user.id,
        )
    )
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Practice attempt not found")
    return attempt


def get_attempt_response(db: Session, user: User, attempt_id: UUID) -> dict[str, Any]:
    attempt = get_attempt_or_404(db, user, attempt_id)
    practice_set = get_practice_set_or_404(db, user, attempt.set_id)
    items = _list_items_for_set(db, practice_set)
    items_by_id = {item.id: item for item in items}
    answers = list(
        db.scalars(
            select(PracticeAnswer)
            .where(PracticeAnswer.attempt_id == attempt.id)
            .order_by(PracticeAnswer.created_at.asc())
        ).all()
    )
    return _serialize_attempt(attempt, answers, items_by_id)


def submit_attempt(
    db: Session,
    user: User,
    set_id: UUID,
    payload: PracticeAttemptSubmitRequest,
) -> dict[str, Any]:
    practice_set = get_practice_set_or_404(db, user, set_id)
    items = _list_items_for_set(db, practice_set)
    if not items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Practice set has no items")

    answers_by_item_id = {answer.item_id: answer.answer_json for answer in payload.answers}
    unknown_item_ids = [item_id for item_id in answers_by_item_id if item_id not in {item.id for item in items}]
    if unknown_item_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt contains item ids outside this practice set")

    attempt = PracticeAttempt(
        user_id=user.id,
        set_id=practice_set.id,
        status=AttemptStatus.graded,
    )
    db.add(attempt)
    db.flush()

    total_items = len(items)
    correct_count = 0
    answer_rows: list[PracticeAnswer] = []
    item_results: list[tuple[PracticeItem, bool]] = []
    per_item_score = 100 / max(total_items, 1)

    for item in items:
        submitted_answer = answers_by_item_id.get(item.id)
        is_correct, feedback_text = _evaluate_answer(item, submitted_answer)
        if is_correct:
            correct_count += 1

        answer_record = PracticeAnswer(
            attempt_id=attempt.id,
            item_id=item.id,
            answer_json=submitted_answer,
            is_correct=is_correct,
            score=round(per_item_score if is_correct else 0, 2),
            feedback_text=feedback_text,
        )
        db.add(answer_record)
        db.flush()

        if not is_correct:
            _update_wrong_question(db, user, item, answer_record, feedback_text)

        answer_rows.append(answer_record)
        item_results.append((item, is_correct))

    score = round((correct_count / total_items) * 100, 2)
    attempt.score = score
    attempt.evaluation_json = {
        "correct_count": correct_count,
        "total_items": total_items,
        "accuracy_rate": score,
        "incorrect_item_ids": [str(item.id) for item, is_correct in item_results if not is_correct],
    }
    db.add(attempt)

    _record_progress(
        db,
        user,
        practice_set,
        attempt,
        total_items,
        correct_count,
        payload.duration_minutes,
        item_results,
    )

    db.commit()
    db.refresh(attempt)
    for answer_record in answer_rows:
        db.refresh(answer_record)

    items_by_id = {item.id: item for item in items}
    return _serialize_attempt(attempt, answer_rows, items_by_id)


def list_wrong_questions(
    db: Session,
    user: User,
    subject: str | None = None,
) -> list[dict[str, Any]]:
    statement = (
        select(WrongQuestion, PracticeItem, PracticeSet)
        .join(PracticeItem, PracticeItem.id == WrongQuestion.item_id)
        .join(PracticeSet, PracticeSet.id == PracticeItem.set_id)
        .where(WrongQuestion.user_id == user.id)
        .order_by(WrongQuestion.wrong_count.desc(), WrongQuestion.updated_at.desc())
    )
    if subject:
        statement = statement.where(PracticeSet.subject == subject.strip())

    rows = db.execute(statement).all()
    return [
        {
            "id": wrong.id,
            "item_id": wrong.item_id,
            "practice_set_id": practice_set.id,
            "stem": item.stem,
            "wrong_count": wrong.wrong_count,
            "last_feedback": wrong.last_feedback,
            "knowledge_points_json": item.knowledge_points_json,
            "created_at": wrong.created_at,
            "updated_at": wrong.updated_at,
        }
        for wrong, item, practice_set in rows
    ]
