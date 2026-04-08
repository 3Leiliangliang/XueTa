from __future__ import annotations

from pathlib import Path
import re
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete as sql_delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import UploadedFile
from app.models.knowledge import KnowledgeBase, KnowledgeChunk, KnowledgeDocument
from app.models.user import User
from app.schemas.kb import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseUpdateRequest,
    KnowledgeDocumentCreateRequest,
    KnowledgeDocumentUpdateRequest,
    KnowledgeRetrieveRequest,
)


TEXT_FILE_EXTENSIONS = {".txt", ".md", ".markdown", ".csv", ".json", ".py", ".js", ".ts", ".html", ".htm"}
MAX_CHUNK_SIZE = 700


def _storage_root() -> Path:
    configured = Path(settings.local_storage_path)
    if configured.is_absolute():
        root = configured
    else:
        backend_root = Path(__file__).resolve().parents[3]
        root = backend_root / configured
    root.mkdir(parents=True, exist_ok=True)
    return root


def _resolve_uploaded_file_path(file_record: UploadedFile) -> Path:
    root = _storage_root().resolve()
    file_path = (root / file_record.storage_path).resolve()
    if root != file_path and root not in file_path.parents:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored file path is invalid",
        )
    return file_path


def _extract_text_from_upload(file_record: UploadedFile | None) -> str | None:
    if file_record is None:
        return None

    extension = f".{file_record.extension.lower()}" if file_record.extension else ""
    mime_type = (file_record.mime_type or "").lower()
    is_text_file = extension in TEXT_FILE_EXTENSIONS or mime_type.startswith("text/") or "json" in mime_type
    if not is_text_file:
        return None

    file_path = _resolve_uploaded_file_path(file_record)
    if not file_path.exists():
        return None

    return file_path.read_text(encoding="utf-8", errors="ignore")


def _split_long_text(text: str, chunk_size: int = MAX_CHUNK_SIZE) -> list[str]:
    return [text[index:index + chunk_size].strip() for index in range(0, len(text), chunk_size) if text[index:index + chunk_size].strip()]


def _chunk_text(content_text: str) -> list[str]:
    normalized = content_text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", normalized) if paragraph.strip()]
    if not paragraphs:
        return _split_long_text(normalized)

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > MAX_CHUNK_SIZE:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_text(paragraph))
            continue

        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= MAX_CHUNK_SIZE:
            current = candidate
        else:
            chunks.append(current.strip())
            current = paragraph

    if current:
        chunks.append(current.strip())

    return chunks


def _serialize_base(base: KnowledgeBase, document_count: int) -> dict[str, Any]:
    return {
        "id": base.id,
        "name": base.name,
        "description": base.description,
        "subject": base.subject,
        "is_public": base.is_public,
        "document_count": document_count,
        "created_at": base.created_at,
        "updated_at": base.updated_at,
    }


def _serialize_document(document: KnowledgeDocument, chunk_count: int) -> dict[str, Any]:
    return {
        "id": document.id,
        "knowledge_base_id": document.knowledge_base_id,
        "uploaded_file_id": document.uploaded_file_id,
        "title": document.title,
        "source_type": document.source_type,
        "source_url": document.source_url,
        "mime_type": document.mime_type,
        "content_text": document.content_text,
        "tags": document.tags,
        "metadata_json": document.metadata_json,
        "chunk_count": chunk_count,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }


def _sync_document_chunks(db: Session, document: KnowledgeDocument) -> list[KnowledgeChunk]:
    db.execute(sql_delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))

    chunks: list[KnowledgeChunk] = []
    for index, content in enumerate(_chunk_text(document.content_text or "")):
        chunk = KnowledgeChunk(
            document_id=document.id,
            chunk_index=index,
            content=content,
            metadata_json={"length": len(content)},
        )
        db.add(chunk)
        chunks.append(chunk)
    return chunks


def list_knowledge_bases(db: Session, user: User, subject: str | None = None) -> list[dict[str, Any]]:
    statement = (
        select(KnowledgeBase, func.count(KnowledgeDocument.id))
        .outerjoin(KnowledgeDocument, KnowledgeDocument.knowledge_base_id == KnowledgeBase.id)
        .where(KnowledgeBase.user_id == user.id)
        .group_by(KnowledgeBase.id)
        .order_by(KnowledgeBase.created_at.desc())
    )
    if subject:
        statement = statement.where(KnowledgeBase.subject == subject.strip())

    rows = db.execute(statement).all()
    return [_serialize_base(base, int(document_count or 0)) for base, document_count in rows]


def get_knowledge_base_or_404(db: Session, user: User, base_id: UUID) -> KnowledgeBase:
    base = db.scalar(
        select(KnowledgeBase).where(
            KnowledgeBase.id == base_id,
            KnowledgeBase.user_id == user.id,
        )
    )
    if base is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    return base


def get_knowledge_base_response(db: Session, user: User, base_id: UUID) -> dict[str, Any]:
    base = get_knowledge_base_or_404(db, user, base_id)
    document_count = int(
        db.scalar(select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.knowledge_base_id == base.id)) or 0
    )
    return _serialize_base(base, document_count)


def create_knowledge_base(db: Session, user: User, payload: KnowledgeBaseCreateRequest) -> dict[str, Any]:
    base = KnowledgeBase(user_id=user.id, **payload.model_dump())
    db.add(base)
    db.commit()
    db.refresh(base)
    return _serialize_base(base, 0)


def update_knowledge_base(
    db: Session,
    base: KnowledgeBase,
    payload: KnowledgeBaseUpdateRequest,
) -> dict[str, Any]:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(base, field, value)
    db.add(base)
    db.commit()
    db.refresh(base)
    document_count = int(
        db.scalar(select(func.count(KnowledgeDocument.id)).where(KnowledgeDocument.knowledge_base_id == base.id)) or 0
    )
    return _serialize_base(base, document_count)


def delete_knowledge_base(db: Session, base: KnowledgeBase) -> None:
    db.delete(base)
    db.commit()


def _get_uploaded_file_for_user(db: Session, user: User, uploaded_file_id: UUID | None) -> UploadedFile | None:
    if uploaded_file_id is None:
        return None
    file_record = db.scalar(
        select(UploadedFile).where(
            UploadedFile.id == uploaded_file_id,
            UploadedFile.user_id == user.id,
        )
    )
    if file_record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uploaded file not found")
    return file_record


def list_documents(
    db: Session,
    user: User,
    knowledge_base_id: UUID | None = None,
    keyword: str | None = None,
) -> list[dict[str, Any]]:
    statement = (
        select(KnowledgeDocument, func.count(KnowledgeChunk.id))
        .join(KnowledgeBase, KnowledgeBase.id == KnowledgeDocument.knowledge_base_id)
        .outerjoin(KnowledgeChunk, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .where(KnowledgeBase.user_id == user.id)
        .group_by(KnowledgeDocument.id)
        .order_by(KnowledgeDocument.updated_at.desc())
    )
    if knowledge_base_id is not None:
        statement = statement.where(KnowledgeDocument.knowledge_base_id == knowledge_base_id)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        statement = statement.where(
            or_(
                KnowledgeDocument.title.ilike(pattern),
                KnowledgeDocument.content_text.ilike(pattern),
            )
        )

    rows = db.execute(statement).all()
    return [_serialize_document(document, int(chunk_count or 0)) for document, chunk_count in rows]


def get_document_or_404(db: Session, user: User, document_id: UUID) -> KnowledgeDocument:
    document = db.scalar(
        select(KnowledgeDocument)
        .join(KnowledgeBase, KnowledgeBase.id == KnowledgeDocument.knowledge_base_id)
        .where(
            KnowledgeDocument.id == document_id,
            KnowledgeBase.user_id == user.id,
        )
    )
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge document not found")
    return document


def get_document_response(db: Session, user: User, document_id: UUID) -> dict[str, Any]:
    document = get_document_or_404(db, user, document_id)
    chunk_count = int(db.scalar(select(func.count(KnowledgeChunk.id)).where(KnowledgeChunk.document_id == document.id)) or 0)
    return _serialize_document(document, chunk_count)


def create_document(db: Session, user: User, payload: KnowledgeDocumentCreateRequest) -> dict[str, Any]:
    base = get_knowledge_base_or_404(db, user, payload.knowledge_base_id)
    file_record = _get_uploaded_file_for_user(db, user, payload.uploaded_file_id)

    content_text = payload.content_text if payload.content_text is not None else _extract_text_from_upload(file_record)
    mime_type = payload.mime_type or (file_record.mime_type if file_record else None)

    document = KnowledgeDocument(
        knowledge_base_id=base.id,
        uploaded_file_id=payload.uploaded_file_id,
        title=payload.title,
        source_type=payload.source_type,
        source_url=payload.source_url,
        mime_type=mime_type,
        content_text=content_text,
        tags=payload.tags,
        metadata_json=payload.metadata_json,
    )
    db.add(document)
    db.flush()
    chunks = _sync_document_chunks(db, document)
    db.commit()
    db.refresh(document)
    return _serialize_document(document, len(chunks))


def update_document(
    db: Session,
    user: User,
    document: KnowledgeDocument,
    payload: KnowledgeDocumentUpdateRequest,
) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    next_base_id = updates.get("knowledge_base_id", document.knowledge_base_id)
    if next_base_id != document.knowledge_base_id:
        get_knowledge_base_or_404(db, user, next_base_id)

    next_uploaded_file_id = updates.get("uploaded_file_id", document.uploaded_file_id)
    file_record = _get_uploaded_file_for_user(db, user, next_uploaded_file_id)

    for field, value in updates.items():
        setattr(document, field, value)

    if "mime_type" not in updates and file_record is not None:
        document.mime_type = file_record.mime_type

    if "content_text" in updates:
        content_text = updates["content_text"]
    else:
        content_text = document.content_text

    if content_text is None and file_record is not None:
        content_text = _extract_text_from_upload(file_record)
    document.content_text = content_text

    db.add(document)
    db.flush()
    chunks = _sync_document_chunks(db, document)
    db.commit()
    db.refresh(document)
    return _serialize_document(document, len(chunks))


def delete_document(db: Session, document: KnowledgeDocument) -> None:
    db.delete(document)
    db.commit()


def list_document_chunks(db: Session, user: User, document_id: UUID) -> list[KnowledgeChunk]:
    document = get_document_or_404(db, user, document_id)
    return list(
        db.scalars(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document.id)
            .order_by(KnowledgeChunk.chunk_index.asc())
        ).all()
    )


def _tokenize_query(query: str) -> list[str]:
    query = query.strip().lower()
    if not query:
        return []
    tokens = {query}
    tokens.update(token.strip().lower() for token in query.split() if token.strip())
    return sorted(tokens, key=len, reverse=True)


def _score_hit(query: str, tokens: list[str], title: str, content: str) -> float:
    title_lower = title.lower()
    content_lower = content.lower()
    score = 0.0
    for token in tokens:
        score += title_lower.count(token) * 6
        score += content_lower.count(token) * 3
    if query in title_lower:
        score += 12
    if query in content_lower:
        score += 8
    return round(score, 2)


def retrieve_knowledge(db: Session, user: User, payload: KnowledgeRetrieveRequest) -> dict[str, Any]:
    query = payload.query.strip().lower()
    tokens = _tokenize_query(payload.query)
    if not tokens:
        return {"query": payload.query, "total_hits": 0, "hits": []}

    patterns = [f"%{token}%" for token in tokens]
    conditions = []
    for pattern in patterns:
        conditions.append(KnowledgeChunk.content.ilike(pattern))
        conditions.append(KnowledgeDocument.title.ilike(pattern))

    statement = (
        select(KnowledgeChunk, KnowledgeDocument, KnowledgeBase)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .join(KnowledgeBase, KnowledgeBase.id == KnowledgeDocument.knowledge_base_id)
        .where(KnowledgeBase.user_id == user.id)
        .where(or_(*conditions))
    )
    if payload.knowledge_base_id is not None:
        statement = statement.where(KnowledgeBase.id == payload.knowledge_base_id)
    if payload.subject:
        statement = statement.where(KnowledgeBase.subject == payload.subject.strip())

    rows = db.execute(statement).all()
    hits = []
    for chunk, document, base in rows:
        score = _score_hit(query, tokens, document.title, chunk.content)
        if score <= 0:
            continue
        hits.append(
            {
                "knowledge_base_id": base.id,
                "document_id": document.id,
                "document_title": document.title,
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "source_type": document.source_type,
                "score": score,
                "tags": document.tags,
            }
        )

    hits.sort(key=lambda item: (item["score"], item["chunk_index"] * -1), reverse=True)
    hits = hits[: payload.limit]
    return {
        "query": payload.query,
        "total_hits": len(hits),
        "hits": hits,
    }
