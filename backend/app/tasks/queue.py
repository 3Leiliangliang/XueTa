from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.redis import get_redis_client

TASK_QUEUE_KEY = "xueta:tasks:queue"
TASK_KEY_PREFIX = "xueta:tasks:task:"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_key(task_id: str) -> str:
    return f"{TASK_KEY_PREFIX}{task_id}"


def enqueue_task(task_name: str, payload: dict[str, Any] | None = None, user_id: str | None = None) -> str:
    client = get_redis_client()
    task_id = str(uuid4())
    task_payload = payload or {}
    task_key = _task_key(task_id)
    client.hset(
        task_key,
        mapping={
            "task_id": task_id,
            "task_name": task_name,
            "status": "queued",
            "payload": json.dumps(task_payload, ensure_ascii=False),
            "result": "",
            "error": "",
            "created_at": _utc_now(),
            "started_at": "",
            "finished_at": "",
            "user_id": user_id or "",
        },
    )
    client.rpush(TASK_QUEUE_KEY, task_id)
    return task_id


def get_task_status(task_id: str) -> dict[str, Any] | None:
    client = get_redis_client()
    task_key = _task_key(task_id)
    if not client.exists(task_key):
        return None
    raw = client.hgetall(task_key)
    payload = _loads_json(raw.get("payload", ""))
    result = _loads_json(raw.get("result", ""))
    return {
        "task_id": raw.get("task_id", task_id),
        "task_name": raw.get("task_name", ""),
        "status": raw.get("status", "unknown"),
        "payload": payload,
        "result": result,
        "error": raw.get("error") or None,
        "created_at": raw.get("created_at"),
        "started_at": raw.get("started_at") or None,
        "finished_at": raw.get("finished_at") or None,
        "user_id": raw.get("user_id") or None,
    }


def update_task(
    task_id: str,
    *,
    status: str | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
) -> None:
    client = get_redis_client()
    task_key = _task_key(task_id)
    updates: dict[str, Any] = {}
    if status is not None:
        updates["status"] = status
    if result is not None:
        updates["result"] = json.dumps(result, ensure_ascii=False)
    if error is not None:
        updates["error"] = error
    if started_at is not None:
        updates["started_at"] = started_at
    if finished_at is not None:
        updates["finished_at"] = finished_at
    if updates:
        client.hset(task_key, mapping=updates)


def _loads_json(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None
