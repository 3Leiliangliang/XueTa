from fastapi import APIRouter

from app.api.v1 import (
    auth,
    chat,
    desktop,
    files,
    health,
    kb,
    notes,
    planner,
    practice,
    progress,
    users,
)


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(planner.router, prefix="/planner", tags=["planner"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(kb.router, prefix="/kb", tags=["knowledge-base"])
api_router.include_router(practice.router, prefix="/practice", tags=["practice"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(desktop.router, prefix="/desktop", tags=["desktop"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
