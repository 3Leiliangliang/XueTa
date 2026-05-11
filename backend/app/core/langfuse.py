from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_langfuse_client():
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None

    try:
        from langfuse import Langfuse
    except Exception as exc:  # pragma: no cover - optional dependency at runtime
        logger.warning("Langfuse client is unavailable: %s", exc)
        return None

    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


def safe_log_generation(
    *,
    name: str,
    model: str,
    input_payload: dict[str, Any] | None,
    output_payload: dict[str, Any] | None,
    metadata: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> None:
    client = get_langfuse_client()
    if client is None:
        return

    try:
        trace = client.trace(name=name, metadata=metadata or {}, tags=tags or [])
        generation = trace.generation(
            name=name,
            model=model,
            input=input_payload,
            output=output_payload,
            metadata=metadata or {},
        )
        generation.end(output=output_payload)
    except Exception as exc:  # pragma: no cover - depends on network/runtime
        logger.warning("Langfuse logging failed: %s", exc)
