from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.note import Note, Notebook, NoteSummary, NoteTodo
from app.models.user import User
from app.schemas.note import (
    NotebookCreateRequest,
    NotebookUpdateRequest,
    NoteCreateRequest,
    NoteTodoCreateRequest,
    NoteTodoUpdateRequest,
    NoteUpdateRequest,
)
from app.services.llm.service import generate_note_summary


def _update_notebook_note_count(db: Session, notebook_id: UUID | None) -> None:
    if notebook_id is None:
        return
    notebook = db.scalar(select(Notebook).where(Notebook.id == notebook_id))
    if notebook is None:
        return
    notebook.note_count = int(
        db.scalar(select(func.count(Note.id)).where(Note.notebook_id == notebook_id)) or 0
    )
    db.add(notebook)


def list_notebooks(db: Session, user: User) -> list[Notebook]:
    statement = (
        select(Notebook)
        .where(Notebook.user_id == user.id)
        .order_by(Notebook.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_notebook_or_404(db: Session, user: User, notebook_id: UUID) -> Notebook:
    notebook = db.scalar(
        select(Notebook).where(Notebook.id == notebook_id, Notebook.user_id == user.id)
    )
    if notebook is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notebook not found")
    return notebook


def create_notebook(db: Session, user: User, payload: NotebookCreateRequest) -> Notebook:
    notebook = Notebook(user_id=user.id, note_count=0, **payload.model_dump())
    db.add(notebook)
    db.commit()
    db.refresh(notebook)
    return notebook


def update_notebook(db: Session, notebook: Notebook, payload: NotebookUpdateRequest) -> Notebook:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(notebook, field, value)
    db.add(notebook)
    db.commit()
    db.refresh(notebook)
    return notebook


def delete_notebook(db: Session, notebook: Notebook) -> None:
    db.delete(notebook)
    db.commit()


def list_notes(
    db: Session,
    user: User,
    notebook_id: UUID | None = None,
    keyword: str | None = None,
) -> list[Note]:
    statement = select(Note).where(Note.user_id == user.id)
    if notebook_id is not None:
        statement = statement.where(Note.notebook_id == notebook_id)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        statement = statement.where(
            or_(Note.title.ilike(pattern), Note.content_markdown.ilike(pattern))
        )
    statement = statement.order_by(Note.updated_at.desc())
    return list(db.scalars(statement).all())


def get_note_or_404(db: Session, user: User, note_id: UUID) -> Note:
    note = db.scalar(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


def create_note(db: Session, user: User, payload: NoteCreateRequest) -> Note:
    if payload.notebook_id is not None:
        get_notebook_or_404(db, user, payload.notebook_id)

    note = Note(user_id=user.id, summary=None, **payload.model_dump())
    db.add(note)
    db.flush()
    _update_notebook_note_count(db, payload.notebook_id)
    db.commit()
    db.refresh(note)
    return note


def update_note(db: Session, user: User, note: Note, payload: NoteUpdateRequest) -> Note:
    previous_notebook_id = note.notebook_id
    updates = payload.model_dump(exclude_unset=True)
    next_notebook_id = updates.get("notebook_id", note.notebook_id)
    if next_notebook_id is not None:
        get_notebook_or_404(db, user, next_notebook_id)

    for field, value in updates.items():
        setattr(note, field, value)
    db.add(note)
    db.flush()

    if previous_notebook_id != note.notebook_id:
        _update_notebook_note_count(db, previous_notebook_id)
        _update_notebook_note_count(db, note.notebook_id)

    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note: Note) -> None:
    notebook_id = note.notebook_id
    db.delete(note)
    db.flush()
    _update_notebook_note_count(db, notebook_id)
    db.commit()


def list_note_todos(db: Session, note: Note) -> list[NoteTodo]:
    statement = (
        select(NoteTodo)
        .where(NoteTodo.note_id == note.id)
        .order_by(NoteTodo.sort_order.asc(), NoteTodo.created_at.asc())
    )
    return list(db.scalars(statement).all())


def get_note_todo_or_404(db: Session, user: User, todo_id: UUID) -> NoteTodo:
    todo = db.scalar(
        select(NoteTodo)
        .join(Note, Note.id == NoteTodo.note_id)
        .where(NoteTodo.id == todo_id, Note.user_id == user.id)
    )
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note todo not found")
    return todo


def create_note_todo(db: Session, note: Note, payload: NoteTodoCreateRequest) -> NoteTodo:
    todo = NoteTodo(note_id=note.id, **payload.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def update_note_todo(db: Session, todo: NoteTodo, payload: NoteTodoUpdateRequest) -> NoteTodo:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(todo, field, value)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def delete_note_todo(db: Session, todo: NoteTodo) -> None:
    db.delete(todo)
    db.commit()


def _build_rule_based_note_summary(note: Note) -> tuple[str, dict]:
    lines = [line.strip() for line in note.content_markdown.splitlines() if line.strip()]
    headline = lines[0] if lines else note.title
    key_points = lines[1:4]
    summary_parts = [f"这份笔记主要围绕“{headline[:80]}”展开。"]
    if key_points:
        summary_parts.append("重点内容包括：")
        summary_parts.extend([f"- {item[:120]}" for item in key_points])
    else:
        summary_parts.append("建议继续补充关键概念、例题与易错点，方便后续复习。")

    suggestions = {
        "suggestions": [
            "补充 1-2 道典型例题和解题步骤",
            "补充一个容易混淆的知识点提醒",
            "把当前笔记拆成更清晰的小标题结构",
        ]
    }
    return "\n".join(summary_parts), suggestions


def summarize_note(db: Session, note: Note) -> NoteSummary:
    llm_result = generate_note_summary(
        title=note.title,
        content_markdown=note.content_markdown,
    )
    if llm_result is None:
        summary_text, suggestions = _build_rule_based_note_summary(note)
        model_name = "rule-based-draft"
    else:
        summary_text, suggestions, model_name = llm_result

    note.summary = summary_text
    summary = NoteSummary(
        note_id=note.id,
        model_name=model_name,
        summary_text=summary_text,
        suggestions_json=suggestions,
    )
    db.add_all([note, summary])
    db.commit()
    db.refresh(summary)
    return summary
