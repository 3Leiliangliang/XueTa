from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.file import UploadedFileResponse
from app.services.files.service import (
    build_download_response,
    delete_uploaded_file,
    get_uploaded_file_or_404,
    list_uploaded_files,
    save_uploaded_file,
)


router = APIRouter()


@router.get("", response_model=list[UploadedFileResponse])
def get_uploaded_files(
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UploadedFileResponse]:
    files = list_uploaded_files(db, current_user, keyword)
    return [UploadedFileResponse.model_validate(file_record) for file_record in files]


@router.post("/upload", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadedFileResponse:
    file_record = await save_uploaded_file(db, current_user, upload)
    return UploadedFileResponse.model_validate(file_record)


@router.get("/{file_id}", response_model=UploadedFileResponse)
def get_uploaded_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UploadedFileResponse:
    file_record = get_uploaded_file_or_404(db, current_user, file_id)
    return UploadedFileResponse.model_validate(file_record)


@router.get("/{file_id}/download")
def download_uploaded_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    file_record = get_uploaded_file_or_404(db, current_user, file_id)
    return build_download_response(file_record)


@router.delete("/{file_id}", response_model=MessageResponse)
def delete_uploaded_file_endpoint(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    file_record = get_uploaded_file_or_404(db, current_user, file_id)
    delete_uploaded_file(db, file_record)
    return MessageResponse(message="Uploaded file deleted successfully")
