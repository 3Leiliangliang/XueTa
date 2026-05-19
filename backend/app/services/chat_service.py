from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import ChatFeedback, ChatMessage, ChatSession, ChatSessionStatus, MessageRole
from app.models.user import User
from app.schemas.chat import (
    ChatFeedbackRequest,
    ChatMessageCreateRequest,
    ChatSessionCreateRequest,
    ChatSessionUpdateRequest,
)
from app.schemas.kb import KnowledgeRetrieveRequest
from app.services.llm.service import generate_chat_reply, has_configured_llm
from app.services.rag.service import retrieve_knowledge

STREAM_CHUNK_SIZE = 48
RAG_RETRIEVE_LIMIT = 4


def _build_rule_based_reply(
    question: str,
    subject: str | None = None,
    citations: list[dict] | None = None,
) -> str:
    topic = subject or "当前问题"
    clean_question = question.strip()
    response = (
        f"我已经收到你关于“{topic}”的问题：{clean_question}\n\n"
        "你可以先从这三个角度理解：\n"
        "1. 先确认题目考察的核心概念。\n"
        "2. 再拆解解题步骤或知识点之间的关系。\n"
        "3. 最后结合一个小例子验证自己是否真的理解。"
    )
    if citations:
        reference_lines = [
            f"[{index}] {item.get('document_title', '参考资料')}"
            for index, item in enumerate(citations[:3], start=1)
        ]
        response += "\n\n可参考资料：\n" + "\n".join(reference_lines)
    return response


def _build_citations_payload(hits: list[dict]) -> list[dict] | None:
    if not hits:
        return None
    citations = []
    for item in hits[:RAG_RETRIEVE_LIMIT]:
        citations.append(
            {
                "document_id": str(item.get("document_id")) if item.get("document_id") is not None else None,
                "document_title": item.get("document_title"),
                "chunk_id": str(item.get("chunk_id")) if item.get("chunk_id") is not None else None,
                "chunk_index": item.get("chunk_index"),
                "content": item.get("content"),
                "score": item.get("score"),
                "source_type": item.get("source_type"),
            }
        )
    return citations


def _retrieve_rag_hits(db: Session, user: User, session: ChatSession, question: str) -> list[dict]:
    try:
        result = retrieve_knowledge(
            db,
            user,
            KnowledgeRetrieveRequest(
                query=question,
                subject=session.subject,
                limit=RAG_RETRIEVE_LIMIT,
            ),
        )
    except Exception:
        return []
    return result.get("hits", [])


def _touch_session_for_message(session: ChatSession, cleaned_content: str) -> None:
    if not session.title:
        session.title = cleaned_content[:50]
    session.updated_at = datetime.now(UTC)


def prepare_chat_message_context(
    db: Session,
    user: User,
    session: ChatSession,
    payload: ChatMessageCreateRequest,
) -> tuple[str, list[dict], list[dict] | None]:
    cleaned_content = payload.content.strip()
    if not cleaned_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty")

    retrieved_hits = _retrieve_rag_hits(db, user, session, cleaned_content)
    citations_payload = _build_citations_payload(retrieved_hits)
    return cleaned_content, retrieved_hits, citations_payload


def split_message_for_stream(content: str, chunk_size: int = STREAM_CHUNK_SIZE) -> list[str]:
    if not content:
        return []

    tokens = re.findall(r"\S+\s*|\n", content)
    if not tokens:
        return [content]

    chunks: list[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current:
            chunks.append(current)
            current = ""

    def append_text(token: str) -> None:
        nonlocal current
        remaining = token
        while remaining:
            available = chunk_size - len(current)
            if available <= 0:
                flush()
                available = chunk_size

            if len(remaining) <= available:
                current += remaining
                remaining = ""
            else:
                current += remaining[:available]
                remaining = remaining[available:]
                flush()

    for token in tokens:
        if token == "\n":
            append_text(token)
            continue
        append_text(token)

    flush()
    return chunks


def list_sessions(db: Session, user: User) -> list[ChatSession]:
    statement = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list(db.scalars(statement).all())


def get_session_or_404(db: Session, user: User, session_id: UUID) -> ChatSession:
    session = db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return session


def create_session(db: Session, user: User, payload: ChatSessionCreateRequest) -> ChatSession:
    title = payload.title
    if not title and payload.first_message:
        title = payload.first_message.strip()[:50]

    session = ChatSession(
        user_id=user.id,
        title=title,
        subject=payload.subject,
        status=ChatSessionStatus.active,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    if payload.first_message:
        create_message_exchange(
            db,
            user,
            session,
            ChatMessageCreateRequest(content=payload.first_message),
        )
        db.refresh(session)
    return session


def update_session(db: Session, session: ChatSession, payload: ChatSessionUpdateRequest) -> ChatSession:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, session: ChatSession) -> None:
    db.delete(session)
    db.commit()


def list_messages(db: Session, session: ChatSession) -> list[ChatMessage]:
    statement = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    return list(db.scalars(statement).all())


def get_message_or_404(db: Session, user: User, message_id: UUID) -> ChatMessage:
    message = db.scalar(
        select(ChatMessage)
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .where(ChatMessage.id == message_id, ChatSession.user_id == user.id)
    )
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat message not found")
    return message


def create_message_exchange(
    db: Session,
    user: User,
    session: ChatSession,
    payload: ChatMessageCreateRequest,
) -> tuple[ChatMessage, ChatMessage]:
    cleaned_content, retrieved_hits, citations_payload = prepare_chat_message_context(
        db,
        user,
        session,
        payload,
    )
    llm_result = generate_chat_reply(cleaned_content, session.subject, retrieved_hits)
    if llm_result is None:
        if has_configured_llm():
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 模型调用失败，请检查自定义模型 API 或服务端 OPENAI 配置。",
            )
        assistant_content = _build_rule_based_reply(cleaned_content, session.subject, citations_payload)
        model_name = "rule-based-draft"
    else:
        assistant_content, model_name = llm_result

    user_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.user,
        content=cleaned_content,
    )
    assistant_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.assistant,
        content=assistant_content,
        citations_json=citations_payload,
        model_name=model_name,
    )
    _touch_session_for_message(session, cleaned_content)

    db.add_all([user_message, assistant_message, session])
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return user_message, assistant_message


def create_streaming_exchange_shell(
    db: Session,
    user: User,
    session: ChatSession,
    payload: ChatMessageCreateRequest,
    prepared_context: tuple[str, list[dict], list[dict] | None] | None = None,
) -> tuple[str, list[dict], list[dict] | None, ChatMessage, ChatMessage]:
    if prepared_context is None:
        cleaned_content, retrieved_hits, citations_payload = prepare_chat_message_context(
            db,
            user,
            session,
            payload,
        )
    else:
        cleaned_content, retrieved_hits, citations_payload = prepared_context

    user_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.user,
        content=cleaned_content,
    )
    assistant_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.assistant,
        content="",
        citations_json=citations_payload,
        model_name=None,
    )
    _touch_session_for_message(session, cleaned_content)

    db.add_all([user_message, assistant_message, session])
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return cleaned_content, retrieved_hits, citations_payload, user_message, assistant_message


def finalize_streaming_assistant_message(
    db: Session,
    assistant_message: ChatMessage,
    *,
    content: str,
    model_name: str,
    citations_payload: list[dict] | None,
) -> ChatMessage:
    assistant_message.content = content
    assistant_message.model_name = model_name
    assistant_message.citations_json = citations_payload
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message


def add_feedback(
    db: Session,
    message: ChatMessage,
    payload: ChatFeedbackRequest,
) -> ChatFeedback:
    feedback = ChatFeedback(
        message_id=message.id,
        value=payload.value,
        reason=payload.reason,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
