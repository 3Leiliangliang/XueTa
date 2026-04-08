from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.kb import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdateRequest,
    KnowledgeChunkResponse,
    KnowledgeDocumentCreateRequest,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUpdateRequest,
    KnowledgeRetrieveRequest,
    KnowledgeRetrieveResponse,
)
from app.services.rag.service import (
    create_document,
    create_knowledge_base,
    delete_document,
    delete_knowledge_base,
    get_document_or_404,
    get_document_response,
    get_knowledge_base_or_404,
    get_knowledge_base_response,
    list_document_chunks,
    list_documents,
    list_knowledge_bases,
    retrieve_knowledge,
    update_document,
    update_knowledge_base,
)


router = APIRouter()


@router.get("/bases", response_model=list[KnowledgeBaseResponse])
def get_knowledge_bases(
    subject: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeBaseResponse]:
    bases = list_knowledge_bases(db, current_user, subject)
    return [KnowledgeBaseResponse.model_validate(base) for base in bases]


@router.post("/bases", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base_endpoint(
    payload: KnowledgeBaseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeBaseResponse:
    base = create_knowledge_base(db, current_user, payload)
    return KnowledgeBaseResponse.model_validate(base)


@router.get("/bases/{base_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    base_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeBaseResponse:
    base = get_knowledge_base_response(db, current_user, base_id)
    return KnowledgeBaseResponse.model_validate(base)


@router.patch("/bases/{base_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base_endpoint(
    base_id: UUID,
    payload: KnowledgeBaseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeBaseResponse:
    base = get_knowledge_base_or_404(db, current_user, base_id)
    updated_base = update_knowledge_base(db, base, payload)
    return KnowledgeBaseResponse.model_validate(updated_base)


@router.delete("/bases/{base_id}", response_model=MessageResponse)
def delete_knowledge_base_endpoint(
    base_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    base = get_knowledge_base_or_404(db, current_user, base_id)
    delete_knowledge_base(db, base)
    return MessageResponse(message="Knowledge base deleted successfully")


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
def get_documents(
    knowledge_base_id: UUID | None = Query(default=None),
    keyword: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeDocumentResponse]:
    documents = list_documents(db, current_user, knowledge_base_id, keyword)
    return [KnowledgeDocumentResponse.model_validate(document) for document in documents]


@router.post("/documents", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document_endpoint(
    payload: KnowledgeDocumentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeDocumentResponse:
    document = create_document(db, current_user, payload)
    return KnowledgeDocumentResponse.model_validate(document)


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeDocumentResponse:
    document = get_document_response(db, current_user, document_id)
    return KnowledgeDocumentResponse.model_validate(document)


@router.patch("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
def update_document_endpoint(
    document_id: UUID,
    payload: KnowledgeDocumentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeDocumentResponse:
    document = get_document_or_404(db, current_user, document_id)
    updated_document = update_document(db, current_user, document, payload)
    return KnowledgeDocumentResponse.model_validate(updated_document)


@router.delete("/documents/{document_id}", response_model=MessageResponse)
def delete_document_endpoint(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    document = get_document_or_404(db, current_user, document_id)
    delete_document(db, document)
    return MessageResponse(message="Knowledge document deleted successfully")


@router.get("/documents/{document_id}/chunks", response_model=list[KnowledgeChunkResponse])
def get_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeChunkResponse]:
    chunks = list_document_chunks(db, current_user, document_id)
    return [KnowledgeChunkResponse.model_validate(chunk) for chunk in chunks]


@router.post("/retrieve", response_model=KnowledgeRetrieveResponse)
def retrieve(
    payload: KnowledgeRetrieveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeRetrieveResponse:
    result = retrieve_knowledge(db, current_user, payload)
    return KnowledgeRetrieveResponse.model_validate(result)
