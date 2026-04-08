from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user, get_db
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
    get_message_or_404,
    get_session_or_404,
    list_messages,
    list_sessions,
    split_message_for_stream,
    create_session,
    delete_session,
    update_session,
)


router = APIRouter()


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
    user_message, assistant_message = create_message_exchange(db, session, payload)
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
) -> EventSourceResponse:
    session = get_session_or_404(db, current_user, session_id)
    user_message, assistant_message = create_message_exchange(db, session, payload)
    user_payload = ChatMessageResponse.model_validate(user_message).model_dump(mode="json")
    assistant_payload = ChatMessageResponse.model_validate(assistant_message).model_dump(mode="json")
    chunks = split_message_for_stream(assistant_message.content)

    async def event_publisher():
        yield {
            "event": "message_start",
            "data": json.dumps(
                {
                    "session_id": str(session.id),
                    "user_message": user_payload,
                    "assistant_message_id": assistant_payload["id"],
                    "chunk_count": len(chunks),
                },
                ensure_ascii=False,
            ),
        }

        for index, chunk in enumerate(chunks):
            yield {
                "event": "delta",
                "data": json.dumps(
                    {
                        "index": index,
                        "delta": chunk,
                    },
                    ensure_ascii=False,
                ),
            }
            await asyncio.sleep(0)

        yield {
            "event": "message_end",
            "data": json.dumps(
                {
                    "assistant_message": assistant_payload,
                },
                ensure_ascii=False,
            ),
        }
        yield {
            "event": "done",
            "data": json.dumps({"ok": True}, ensure_ascii=False),
        }

    return EventSourceResponse(event_publisher())


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
