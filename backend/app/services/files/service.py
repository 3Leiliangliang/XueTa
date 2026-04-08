from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import UploadedFile
from app.models.user import User


def _storage_root() -> Path:
    configured = Path(settings.local_storage_path)
    if configured.is_absolute():
        root = configured
    else:
        backend_root = Path(__file__).resolve().parents[3]
        root = backend_root / configured
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_storage_path(file_record: UploadedFile) -> Path:
    root = _storage_root().resolve()
    file_path = (root / file_record.storage_path).resolve()
    if root != file_path and root not in file_path.parents:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored file path is invalid",
        )
    return file_path


def list_uploaded_files(
    db: Session,
    user: User,
    keyword: str | None = None,
) -> list[UploadedFile]:
    statement = select(UploadedFile).where(UploadedFile.user_id == user.id)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        statement = statement.where(
            or_(
                UploadedFile.original_filename.ilike(pattern),
                UploadedFile.filename.ilike(pattern),
            )
        )
    statement = statement.order_by(UploadedFile.created_at.desc())
    return list(db.scalars(statement).all())


def get_uploaded_file_or_404(db: Session, user: User, file_id: UUID) -> UploadedFile:
    file_record = db.scalar(
        select(UploadedFile).where(
            UploadedFile.id == file_id,
            UploadedFile.user_id == user.id,
        )
    )
    if file_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file not found")
    return file_record


async def save_uploaded_file(db: Session, user: User, upload: UploadFile) -> UploadedFile:
    original_filename = upload.filename or "upload.bin"
    suffix = Path(original_filename).suffix.lower()
    extension = suffix.lstrip(".") or None
    generated_name = f"{uuid.uuid4().hex}{suffix}"

    relative_path = Path("uploads") / str(user.id) / generated_name
    storage_path = _storage_root() / relative_path
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    checksum = hashlib.sha256()
    size_bytes = 0

    try:
        with storage_path.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                checksum.update(chunk)
                size_bytes += len(chunk)
                output.write(chunk)
    except Exception as exc:
        if storage_path.exists():
            storage_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist uploaded file",
        ) from exc
    finally:
        await upload.close()

    metadata_json = None
    if upload.content_type:
        metadata_json = {"content_type": upload.content_type}

    file_record = UploadedFile(
        user_id=user.id,
        filename=generated_name,
        original_filename=original_filename,
        mime_type=upload.content_type,
        extension=extension,
        size_bytes=size_bytes,
        storage_path=relative_path.as_posix(),
        checksum=checksum.hexdigest(),
        metadata_json=metadata_json,
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


def delete_uploaded_file(db: Session, file_record: UploadedFile) -> None:
    storage_path = _resolve_storage_path(file_record)
    if storage_path.exists():
        storage_path.unlink(missing_ok=True)

    db.delete(file_record)
    db.commit()


def build_download_response(file_record: UploadedFile) -> FileResponse:
    storage_path = _resolve_storage_path(file_record)
    if not storage_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file does not exist")

    return FileResponse(
        path=storage_path,
        media_type=file_record.mime_type or "application/octet-stream",
        filename=file_record.original_filename,
    )
