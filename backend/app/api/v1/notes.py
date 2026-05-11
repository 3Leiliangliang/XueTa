from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.note import (
    NotebookCreateRequest,
    NotebookResponse,
    NotebookUpdateRequest,
    NoteCreateRequest,
    NoteResponse,
    NoteSummaryResponse,
    NoteTodoCreateRequest,
    NoteTodoResponse,
    NoteTodoUpdateRequest,
    NoteUpdateRequest,
)
from app.services.notes.service import (
    create_note,
    create_note_todo,
    create_notebook,
    delete_note,
    delete_note_todo,
    delete_notebook,
    get_note_or_404,
    get_note_todo_or_404,
    get_notebook_or_404,
    list_note_todos,
    list_notes,
    list_notebooks,
    summarize_note,
    update_note,
    update_note_todo,
    update_notebook,
)


router = APIRouter()


@router.get("/notebooks", response_model=list[NotebookResponse])
def get_notebooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotebookResponse]:
    return [NotebookResponse.model_validate(book) for book in list_notebooks(db, current_user)]


@router.post("/notebooks", response_model=NotebookResponse, status_code=status.HTTP_201_CREATED)
def create_notebook_endpoint(
    payload: NotebookCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotebookResponse:
    notebook = create_notebook(db, current_user, payload)
    return NotebookResponse.model_validate(notebook)


@router.get("/notebooks/{notebook_id}", response_model=NotebookResponse)
def get_notebook(
    notebook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotebookResponse:
    notebook = get_notebook_or_404(db, current_user, notebook_id)
    return NotebookResponse.model_validate(notebook)


@router.patch("/notebooks/{notebook_id}", response_model=NotebookResponse)
def update_notebook_endpoint(
    notebook_id: UUID,
    payload: NotebookUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotebookResponse:
    notebook = get_notebook_or_404(db, current_user, notebook_id)
    notebook = update_notebook(db, notebook, payload)
    return NotebookResponse.model_validate(notebook)


@router.delete("/notebooks/{notebook_id}", response_model=MessageResponse)
def delete_notebook_endpoint(
    notebook_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    notebook = get_notebook_or_404(db, current_user, notebook_id)
    delete_notebook(db, notebook)
    return MessageResponse(message="Notebook deleted successfully")


@router.get("", response_model=list[NoteResponse])
def get_notes(
    notebook_id: UUID | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NoteResponse]:
    notes = list_notes(db, current_user, notebook_id=notebook_id, keyword=keyword)
    return [NoteResponse.model_validate(note) for note in notes]


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note_endpoint(
    payload: NoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteResponse:
    note = create_note(db, current_user, payload)
    return NoteResponse.model_validate(note)


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteResponse:
    note = get_note_or_404(db, current_user, note_id)
    return NoteResponse.model_validate(note)


@router.patch("/{note_id}", response_model=NoteResponse)
def update_note_endpoint(
    note_id: UUID,
    payload: NoteUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteResponse:
    note = get_note_or_404(db, current_user, note_id)
    note = update_note(db, current_user, note, payload)
    return NoteResponse.model_validate(note)


@router.delete("/{note_id}", response_model=MessageResponse)
def delete_note_endpoint(
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    note = get_note_or_404(db, current_user, note_id)
    delete_note(db, note)
    return MessageResponse(message="Note deleted successfully")


@router.get("/{note_id}/todos", response_model=list[NoteTodoResponse])
def get_note_todos(
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NoteTodoResponse]:
    note = get_note_or_404(db, current_user, note_id)
    todos = list_note_todos(db, note)
    return [NoteTodoResponse.model_validate(todo) for todo in todos]


@router.post("/{note_id}/todos", response_model=NoteTodoResponse, status_code=status.HTTP_201_CREATED)
def create_note_todo_endpoint(
    note_id: UUID,
    payload: NoteTodoCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteTodoResponse:
    note = get_note_or_404(db, current_user, note_id)
    todo = create_note_todo(db, note, payload)
    return NoteTodoResponse.model_validate(todo)


@router.patch("/todos/{todo_id}", response_model=NoteTodoResponse)
def update_note_todo_endpoint(
    todo_id: UUID,
    payload: NoteTodoUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteTodoResponse:
    todo = get_note_todo_or_404(db, current_user, todo_id)
    todo = update_note_todo(db, todo, payload)
    return NoteTodoResponse.model_validate(todo)


@router.delete("/todos/{todo_id}", response_model=MessageResponse)
def delete_note_todo_endpoint(
    todo_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    todo = get_note_todo_or_404(db, current_user, todo_id)
    delete_note_todo(db, todo)
    return MessageResponse(message="Note todo deleted successfully")


@router.post("/{note_id}/summarize", response_model=NoteSummaryResponse, status_code=status.HTTP_201_CREATED)
def summarize_note_endpoint(
    note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NoteSummaryResponse:
    note = get_note_or_404(db, current_user, note_id)
    summary = summarize_note(db, note)
    return NoteSummaryResponse.model_validate(summary)
