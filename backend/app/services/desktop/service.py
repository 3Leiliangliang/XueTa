from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.desktop import DesktopLayout
from app.models.user import User
from app.schemas.desktop import DesktopLayoutCreateRequest, DesktopLayoutUpdateRequest


def list_layouts(db: Session, user: User) -> list[DesktopLayout]:
    statement = (
        select(DesktopLayout)
        .where(DesktopLayout.user_id == user.id)
        .order_by(DesktopLayout.updated_at.desc(), DesktopLayout.created_at.desc())
    )
    return list(db.scalars(statement).all())


def get_layout_or_404(db: Session, user: User, layout_id: UUID) -> DesktopLayout:
    layout = db.scalar(
        select(DesktopLayout).where(
            DesktopLayout.id == layout_id,
            DesktopLayout.user_id == user.id,
        )
    )
    if layout is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Desktop layout not found")
    return layout


def get_layout_by_name_or_latest(
    db: Session,
    user: User,
    name: str | None = None,
) -> DesktopLayout:
    statement = select(DesktopLayout).where(DesktopLayout.user_id == user.id)
    if name:
        statement = statement.where(DesktopLayout.name == name.strip())
    statement = statement.order_by(DesktopLayout.updated_at.desc(), DesktopLayout.created_at.desc())

    layout = db.scalar(statement)
    if layout is None:
        detail = "Desktop layout not found"
        if name:
            detail = f'Desktop layout "{name}" not found'
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return layout


def create_layout(
    db: Session,
    user: User,
    payload: DesktopLayoutCreateRequest,
) -> DesktopLayout:
    layout = DesktopLayout(
        user_id=user.id,
        name=payload.name.strip(),
        layout_json=payload.layout_json,
    )
    db.add(layout)
    db.commit()
    db.refresh(layout)
    return layout


def upsert_layout(
    db: Session,
    user: User,
    payload: DesktopLayoutCreateRequest,
) -> DesktopLayout:
    normalized_name = payload.name.strip()
    layout = db.scalar(
        select(DesktopLayout)
        .where(
            DesktopLayout.user_id == user.id,
            DesktopLayout.name == normalized_name,
        )
        .order_by(DesktopLayout.updated_at.desc(), DesktopLayout.created_at.desc())
    )
    if layout is None:
        return create_layout(db, user, payload)

    layout.name = normalized_name
    layout.layout_json = payload.layout_json
    db.add(layout)
    db.commit()
    db.refresh(layout)
    return layout


def update_layout(
    db: Session,
    layout: DesktopLayout,
    payload: DesktopLayoutUpdateRequest,
) -> DesktopLayout:
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()

    for field, value in updates.items():
        setattr(layout, field, value)

    db.add(layout)
    db.commit()
    db.refresh(layout)
    return layout


def delete_layout(db: Session, layout: DesktopLayout) -> None:
    db.delete(layout)
    db.commit()
