from fastapi import APIRouter, Depends

from app.api.deps import apply_request_llm_config
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
    tasks,
    translate,
    users,
)


api_router = APIRouter(dependencies=[Depends(apply_request_llm_config)])
api_router.include_router(health.router, tags=['health'])
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(users.router, prefix='/users', tags=['users'])
api_router.include_router(planner.router, prefix='/planner', tags=['planner'])
api_router.include_router(notes.router, prefix='/notes', tags=['notes'])
api_router.include_router(chat.router, prefix='/chat', tags=['chat'])
api_router.include_router(translate.router, prefix='/translate', tags=['translate'])
api_router.include_router(kb.router, prefix='/kb', tags=['knowledge-base'])
api_router.include_router(practice.router, prefix='/practice', tags=['practice'])
api_router.include_router(progress.router, prefix='/progress', tags=['progress'])
api_router.include_router(desktop.router, prefix='/desktop', tags=['desktop'])
api_router.include_router(files.router, prefix='/files', tags=['files'])
api_router.include_router(tasks.router, prefix='/tasks', tags=['tasks'])
