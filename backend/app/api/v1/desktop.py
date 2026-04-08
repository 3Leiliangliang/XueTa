from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.desktop import (
    DesktopLayoutCreateRequest,
    DesktopLayoutResponse,
    DesktopLayoutUpdateRequest,
)
from app.services.desktop.service import (
    create_layout,
    delete_layout,
    get_layout_by_name_or_latest,
    get_layout_or_404,
    list_layouts,
    update_layout,
    upsert_layout,
)


router = APIRouter()


@router.get("/layout", response_model=DesktopLayoutResponse)
def get_layout(
    name: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DesktopLayoutResponse:
    layout = get_layout_by_name_or_latest(db, current_user, name)
    return DesktopLayoutResponse.model_validate(layout)


@router.put("/layout", response_model=DesktopLayoutResponse)
def upsert_layout_endpoint(
    payload: DesktopLayoutCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DesktopLayoutResponse:
    layout = upsert_layout(db, current_user, payload)
    return DesktopLayoutResponse.model_validate(layout)


@router.get("/layouts", response_model=list[DesktopLayoutResponse])
def get_layouts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DesktopLayoutResponse]:
    return [DesktopLayoutResponse.model_validate(item) for item in list_layouts(db, current_user)]


@router.post("/layouts", response_model=DesktopLayoutResponse, status_code=status.HTTP_201_CREATED)
def create_layout_endpoint(
    payload: DesktopLayoutCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DesktopLayoutResponse:
    layout = create_layout(db, current_user, payload)
    return DesktopLayoutResponse.model_validate(layout)


@router.get("/layouts/{layout_id}", response_model=DesktopLayoutResponse)
def get_layout_by_id(
    layout_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DesktopLayoutResponse:
    layout = get_layout_or_404(db, current_user, layout_id)
    return DesktopLayoutResponse.model_validate(layout)


@router.patch("/layouts/{layout_id}", response_model=DesktopLayoutResponse)
def update_layout_endpoint(
    layout_id: UUID,
    payload: DesktopLayoutUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DesktopLayoutResponse:
    layout = get_layout_or_404(db, current_user, layout_id)
    layout = update_layout(db, layout, payload)
    return DesktopLayoutResponse.model_validate(layout)


@router.delete("/layouts/{layout_id}", response_model=MessageResponse)
def delete_layout_endpoint(
    layout_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    layout = get_layout_or_404(db, current_user, layout_id)
    delete_layout(db, layout)
    return MessageResponse(message="Desktop layout deleted successfully")
