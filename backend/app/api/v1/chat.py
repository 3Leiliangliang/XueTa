from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.chat import (
    ChatExchangeResponse,
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatMessageCreateRequest,
    ChatMessageResponse,
    ChatSessionCreateRequest,
    ChatSessionResponse,
    ChatSessionUpdateRequest,
)
from app.schemas.common import MessageResponse
from app.services.chat_service import (
    add_feedback,
    create_message_exchange,
    create_streaming_exchange_shell,
    finalize_streaming_assistant_message,
    get_message_or_404,
    get_session_or_404,
    list_messages,
    list_sessions,
    split_message_for_stream,
    create_session,
    delete_session,
    update_session,
    _build_rule_based_reply,
    prepare_chat_message_context,
)
from app.services.llm.service import generate_chat_reply, open_chat_reply_stream


router = APIRouter()


def _sse_event(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_session_endpoint(
    payload: ChatSessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionResponse:
    session = create_session(db, current_user, payload)
    return ChatSessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[ChatSessionResponse])
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSessionResponse]:
    sessions = list_sessions(db, current_user)
    return [ChatSessionResponse.model_validate(session) for session in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionResponse:
    session = get_session_or_404(db, current_user, session_id)
    return ChatSessionResponse.model_validate(session)


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
def update_session_endpoint(
    session_id: UUID,
    payload: ChatSessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionResponse:
    session = get_session_or_404(db, current_user, session_id)
    session = update_session(db, session, payload)
    return ChatSessionResponse.model_validate(session)


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
def delete_session_endpoint(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    session = get_session_or_404(db, current_user, session_id)
    delete_session(db, session)
    return MessageResponse(message="Chat session deleted successfully")


@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_session_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatMessageResponse]:
    session = get_session_or_404(db, current_user, session_id)
    messages = list_messages(db, session)
    return [ChatMessageResponse.model_validate(message) for message in messages]


@router.post("/sessions/{session_id}/messages", response_model=ChatExchangeResponse, status_code=status.HTTP_201_CREATED)
def create_session_message(
    session_id: UUID,
    payload: ChatMessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatExchangeResponse:
    session = get_session_or_404(db, current_user, session_id)
    user_message, assistant_message = create_message_exchange(db, current_user, session, payload)
    return ChatExchangeResponse(
        user_message=ChatMessageResponse.model_validate(user_message),
        assistant_message=ChatMessageResponse.model_validate(assistant_message),
    )


@router.post("/sessions/{session_id}/messages/stream")
def create_session_message_stream(
    session_id: UUID,
    payload: ChatMessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    session = get_session_or_404(db, current_user, session_id)
    prepared_context = prepare_chat_message_context(db, current_user, session, payload)
    cleaned_content, retrieved_hits, citations_payload = prepared_context

    stream_bundle = open_chat_reply_stream(cleaned_content, session.subject, retrieved_hits)
    sync_model_reply = None
    if stream_bundle is None:
        sync_model_reply = generate_chat_reply(cleaned_content, session.subject, retrieved_hits)
        if sync_model_reply is None and settings.openai_api_key:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI 模型调用失败，请检查 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL 配置。",
            )

    cleaned_content, retrieved_hits, citations_payload, user_message, assistant_message = create_streaming_exchange_shell(
        db,
        current_user,
        session,
        payload,
        prepared_context=prepared_context,
    )
    user_payload = ChatMessageResponse.model_validate(user_message).model_dump(mode="json")

    async def event_publisher():
        content_parts: list[str] = []
        model_name = 'rule-based-draft'

        yield _sse_event(
            "message_start",
            {
                "session_id": str(session.id),
                "user_message": user_payload,
                "assistant_message_id": str(assistant_message.id),
                "chunk_count": None,
            },
        )

        if stream_bundle is None:
            if sync_model_reply is not None:
                fallback_content, model_name = sync_model_reply
            else:
                fallback_content = _build_rule_based_reply(cleaned_content, session.subject, citations_payload)
                model_name = 'rule-based-draft'

            for index, chunk in enumerate(split_message_for_stream(fallback_content)):
                content_parts.append(chunk)
                yield _sse_event("delta", {"index": index, "delta": chunk})
                await asyncio.sleep(0)
        else:
            stream_iterator, stream_state = stream_bundle
            model_name = stream_state.get('model_name', model_name)

            def next_delta() -> tuple[str, bool]:
                try:
                    return next(stream_iterator), False
                except StopIteration:
                    return '', True

            index = 0
            while True:
                try:
                    delta, finished = await asyncio.to_thread(next_delta)
                except Exception:
                    break
                if finished:
                    break
                if not delta:
                    continue
                content_parts.append(delta)
                model_name = stream_state.get('model_name', model_name)
                yield _sse_event("delta", {"index": index, "delta": delta})
                index += 1
                await asyncio.sleep(0)

            if not content_parts:
                retry_reply = generate_chat_reply(cleaned_content, session.subject, retrieved_hits)
                if retry_reply is not None:
                    fallback_content, model_name = retry_reply
                elif settings.openai_api_key:
                    fallback_content = "AI 模型调用失败，请检查 OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL 配置。"
                    model_name = 'llm-unavailable'
                else:
                    fallback_content = _build_rule_based_reply(cleaned_content, session.subject, citations_payload)
                    model_name = 'rule-based-draft'
                for offset, chunk in enumerate(split_message_for_stream(fallback_content), start=index):
                    content_parts.append(chunk)
                    yield _sse_event("delta", {"index": offset, "delta": chunk})
                    await asyncio.sleep(0)
            else:
                model_name = stream_state.get('model_name', model_name)

        final_content = ''.join(content_parts)
        finalized_message = finalize_streaming_assistant_message(
            db,
            assistant_message,
            content=final_content,
            model_name=model_name,
            citations_payload=citations_payload,
        )
        assistant_payload = ChatMessageResponse.model_validate(finalized_message).model_dump(mode="json")

        yield _sse_event("message_end", {"assistant_message": assistant_payload})
        yield _sse_event("done", {"ok": True})

    return StreamingResponse(event_publisher(), media_type="text/event-stream")


@router.post("/messages/{message_id}/feedback", response_model=ChatFeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback_endpoint(
    message_id: UUID,
    payload: ChatFeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatFeedbackResponse:
    message = get_message_or_404(db, current_user, message_id)
    feedback = add_feedback(db, message, payload)
    return ChatFeedbackResponse.model_validate(feedback)
