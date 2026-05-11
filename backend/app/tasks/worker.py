from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.redis import get_redis_client
from app.tasks import demo  # noqa: F401
from app.tasks.queue import TASK_QUEUE_KEY, get_task_status, update_task
from app.tasks.registry import get_task


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_worker(poll_timeout: int = 5) -> None:
    client = get_redis_client()
    while True:
        popped = client.brpop(TASK_QUEUE_KEY, timeout=poll_timeout)
        if not popped:
            continue
        _, task_id = popped
        task_data = get_task_status(task_id)
        if not task_data:
            continue
        task_name = task_data.get("task_name") or ""
        payload = task_data.get("payload") or {}
        task_fn = get_task(task_name)
        started_at = _utc_now()
        if task_fn is None:
            update_task(
                task_id,
                status="failed",
                error=f"Task '{task_name}' is not registered",
                started_at=started_at,
                finished_at=_utc_now(),
            )
            continue
        update_task(task_id, status="running", started_at=started_at)
        try:
            result = task_fn(payload)
            update_task(
                task_id,
                status="succeeded",
                result=result or {},
                finished_at=_utc_now(),
            )
        except Exception as exc:  # pragma: no cover - runtime protection
            update_task(
                task_id,
                status="failed",
                error=str(exc),
                finished_at=_utc_now(),
            )


if __name__ == "__main__":
    run_worker()
