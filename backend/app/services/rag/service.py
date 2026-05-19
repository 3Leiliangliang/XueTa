from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete as sql_delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.file import UploadedFile
from app.models.knowledge import (
    KnowledgeBase,
    KnowledgeChunk,
    KnowledgeChunkEmbedding,
    KnowledgeDocument,
)
from app.models.user import User
from app.schemas.kb import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseUpdateRequest,
    KnowledgeDocumentCreateRequest,
    KnowledgeDocumentUpdateRequest,
    KnowledgeRetrieveRequest,
)
from app.services.content_extraction import ContentExtractionError, extract_text_from_path, extract_text_from_url
from app.services.llm.service import EMBEDDING_DIMENSIONS, generate_embedding, generate_embeddings


MAX_CHUNK_SIZE = 700
VECTOR_SCORE_THRESHOLD = 0.12
VECTOR_CANDIDATE_MULTIPLIER = 6


def _fit_embedding_dimensions(vector: list[float]) -> list[float]:
    if len(vector) == EMBEDDING_DIMENSIONS:
        return vector
    if len(vector) > EMBEDDING_DIMENSIONS:
        return vector[:EMBEDDING_DIMENSIONS]
    return [*vector, *([0.0] * (EMBEDDING_DIMENSIONS - len(vector)))]


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


def _extract_text_from_upload(file_record: UploadedFile | None) -> tuple[str | None, dict | None]:
    if file_record is None:
        return None, None

    file_path = _resolve_uploaded_file_path(file_record)
    try:
        return extract_text_from_path(
            file_path,
            mime_type=file_record.mime_type,
            filename=file_record.original_filename,
        )
    except ContentExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc



def _extract_text_from_source_url(source_url: str | None) -> tuple[str | None, dict | None]:
    if not source_url:
        return None, None

    try:
        return extract_text_from_url(source_url)
    except ContentExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


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


def _coerce_embedding_vector(value: Any) -> list[float] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [float(item) for item in value]
    if isinstance(value, tuple):
        return [float(item) for item in value]
    if hasattr(value, 'tolist'):
        return [float(item) for item in value.tolist()]
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, bytes):
        value = value.decode('utf-8', errors='ignore')
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [float(item) for item in parsed]
        if stripped.startswith('[') and stripped.endswith(']'):
            stripped = stripped[1:-1]
        return [float(item.strip()) for item in stripped.split(',') if item.strip()]
    return None


def _cosine_similarity(left: list[float] | None, right: list[float] | None) -> float:
    if not left or not right:
        return 0.0
    if len(left) != len(right):
        size = min(len(left), len(right))
        left = left[:size]
        right = right[:size]
    dot = sum(l * r for l, r in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm <= 0 or right_norm <= 0:
        return 0.0
    similarity = dot / (left_norm * right_norm)
    return max(0.0, float(similarity))


def _sync_document_chunks(db: Session, document: KnowledgeDocument) -> list[KnowledgeChunk]:
    db.execute(sql_delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))

    chunks: list[KnowledgeChunk] = []
    chunk_contents = _chunk_text(document.content_text or "")
    for index, content in enumerate(chunk_contents):
        chunk = KnowledgeChunk(
            document_id=document.id,
            chunk_index=index,
            content=content,
            metadata_json={"length": len(content)},
        )
        db.add(chunk)
        chunks.append(chunk)

    if not chunks:
        return []

    db.flush()
    vectors, embedding_model = generate_embeddings([chunk.content for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        fitted_vector = _fit_embedding_dimensions(vector)
        chunk.metadata_json = {
            **(chunk.metadata_json or {}),
            "embedding_model": embedding_model,
            "embedding_dimensions": len(fitted_vector),
            "original_embedding_dimensions": len(vector),
        }
        db.add(
            KnowledgeChunkEmbedding(
                chunk_id=chunk.id,
                embedding_model=embedding_model,
                dimensions=len(fitted_vector),
                embedding=fitted_vector,
            )
        )

    return chunks


def _merge_metadata(existing: dict | None, extracted: dict | None) -> dict | None:
    metadata = dict(existing or {})
    if extracted:
        metadata["extraction"] = extracted
    return metadata or None


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

    extracted_text = None
    extracted_metadata = None
    if payload.content_text is None:
        if file_record is not None:
            extracted_text, extracted_metadata = _extract_text_from_upload(file_record)
        elif payload.source_url:
            extracted_text, extracted_metadata = _extract_text_from_source_url(payload.source_url)

    content_text = payload.content_text if payload.content_text is not None else extracted_text
    mime_type = payload.mime_type or (extracted_metadata or {}).get('mime_type') or (file_record.mime_type if file_record else None)

    document = KnowledgeDocument(
        knowledge_base_id=base.id,
        uploaded_file_id=payload.uploaded_file_id,
        title=payload.title,
        source_type=payload.source_type,
        source_url=payload.source_url,
        mime_type=mime_type,
        content_text=content_text,
        tags=payload.tags,
        metadata_json=_merge_metadata(payload.metadata_json, extracted_metadata),
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

    extracted_metadata = None
    source_url = document.source_url
    if "content_text" in updates:
        content_text = updates["content_text"]
    elif file_record is not None and ("uploaded_file_id" in updates or document.content_text is None):
        content_text, extracted_metadata = _extract_text_from_upload(file_record)
    elif source_url and ("source_url" in updates or document.content_text is None):
        content_text, extracted_metadata = _extract_text_from_source_url(source_url)
    else:
        content_text = document.content_text

    document.content_text = content_text
    if "mime_type" not in updates:
        document.mime_type = (extracted_metadata or {}).get('mime_type') or (file_record.mime_type if file_record else document.mime_type)
    document.metadata_json = _merge_metadata(document.metadata_json, extracted_metadata)

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


def _build_hit(document: KnowledgeDocument, base: KnowledgeBase, chunk: KnowledgeChunk, score: float) -> dict[str, Any]:
    return {
        "knowledge_base_id": base.id,
        "document_id": document.id,
        "document_title": document.title,
        "chunk_id": chunk.id,
        "chunk_index": chunk.chunk_index,
        "content": chunk.content,
        "source_type": document.source_type,
        "score": round(score, 4),
        "tags": document.tags,
    }


def _apply_retrieve_filters(statement, user: User, payload: KnowledgeRetrieveRequest):
    statement = statement.where(KnowledgeBase.user_id == user.id)
    if payload.knowledge_base_id is not None:
        statement = statement.where(KnowledgeBase.id == payload.knowledge_base_id)
    if payload.subject:
        statement = statement.where(KnowledgeBase.subject == payload.subject.strip())
    return statement


def _retrieve_keyword_hits(db: Session, user: User, payload: KnowledgeRetrieveRequest, query: str, tokens: list[str]) -> list[dict[str, Any]]:
    patterns = [f"%{token}%" for token in tokens]
    conditions = []
    for pattern in patterns:
        conditions.append(KnowledgeChunk.content.ilike(pattern))
        conditions.append(KnowledgeDocument.title.ilike(pattern))

    statement = (
        select(KnowledgeChunk, KnowledgeDocument, KnowledgeBase)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .join(KnowledgeBase, KnowledgeBase.id == KnowledgeDocument.knowledge_base_id)
        .where(or_(*conditions))
    )
    statement = _apply_retrieve_filters(statement, user, payload)
    rows = db.execute(statement).all()

    hits = []
    for chunk, document, base in rows:
        keyword_score = _score_hit(query, tokens, document.title, chunk.content)
        if keyword_score <= 0:
            continue
        hits.append(_build_hit(document, base, chunk, keyword_score))

    hits.sort(key=lambda item: (item["score"], item["chunk_index"] * -1), reverse=True)
    return hits[: payload.limit]


def _retrieve_vector_hits_python(db: Session, user: User, payload: KnowledgeRetrieveRequest, query_vector: list[float], query: str, tokens: list[str]) -> list[dict[str, Any]]:
    statement = (
        select(KnowledgeChunk, KnowledgeDocument, KnowledgeBase, KnowledgeChunkEmbedding)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .join(KnowledgeBase, KnowledgeBase.id == KnowledgeDocument.knowledge_base_id)
        .join(KnowledgeChunkEmbedding, KnowledgeChunkEmbedding.chunk_id == KnowledgeChunk.id)
    )
    statement = _apply_retrieve_filters(statement, user, payload)

    rows = db.execute(statement).all()
    hits = []
    for chunk, document, base, embedding_row in rows:
        vector = _coerce_embedding_vector(embedding_row.embedding)
        vector_score = _cosine_similarity(query_vector, vector)
        keyword_score = _score_hit(query, tokens, document.title, chunk.content)
        if keyword_score <= 0 and vector_score < VECTOR_SCORE_THRESHOLD:
            continue
        combined_score = vector_score * 100 + keyword_score
        hits.append(_build_hit(document, base, chunk, combined_score))

    hits.sort(key=lambda item: (item["score"], item["chunk_index"] * -1), reverse=True)
    return hits[: payload.limit]


def _retrieve_vector_hits_postgres(db: Session, user: User, payload: KnowledgeRetrieveRequest, query_vector: list[float], query: str, tokens: list[str]) -> list[dict[str, Any]]:
    distance_expr = KnowledgeChunkEmbedding.embedding.cosine_distance(query_vector).label('distance')
    statement = (
        select(KnowledgeChunk, KnowledgeDocument, KnowledgeBase, KnowledgeChunkEmbedding, distance_expr)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .join(KnowledgeBase, KnowledgeBase.id == KnowledgeDocument.knowledge_base_id)
        .join(KnowledgeChunkEmbedding, KnowledgeChunkEmbedding.chunk_id == KnowledgeChunk.id)
        .order_by(distance_expr.asc())
        .limit(max(payload.limit * VECTOR_CANDIDATE_MULTIPLIER, payload.limit))
    )
    statement = _apply_retrieve_filters(statement, user, payload)

    rows = db.execute(statement).all()
    hits = []
    for chunk, document, base, _embedding_row, distance in rows:
        vector_score = max(0.0, 1.0 - float(distance))
        keyword_score = _score_hit(query, tokens, document.title, chunk.content)
        if keyword_score <= 0 and vector_score < VECTOR_SCORE_THRESHOLD:
            continue
        combined_score = vector_score * 100 + keyword_score
        hits.append(_build_hit(document, base, chunk, combined_score))

    hits.sort(key=lambda item: (item["score"], item["chunk_index"] * -1), reverse=True)
    return hits[: payload.limit]


def retrieve_knowledge(db: Session, user: User, payload: KnowledgeRetrieveRequest) -> dict[str, Any]:
    query = payload.query.strip().lower()
    tokens = _tokenize_query(payload.query)
    if not query:
        return {"query": payload.query, "total_hits": 0, "hits": []}

    query_vector, _embedding_model = generate_embedding(payload.query)
    query_vector = _fit_embedding_dimensions(query_vector)
    dialect_name = db.bind.dialect.name if db.bind is not None else ''

    if dialect_name == 'postgresql':
        hits = _retrieve_vector_hits_postgres(db, user, payload, query_vector, query, tokens)
    else:
        hits = _retrieve_vector_hits_python(db, user, payload, query_vector, query, tokens)

    if not hits:
        hits = _retrieve_keyword_hits(db, user, payload, query, tokens)

    return {
        "query": payload.query,
        "total_hits": len(hits),
        "hits": hits,
    }
