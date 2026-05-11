from __future__ import annotations

from collections.abc import Callable
from typing import Any

TASK_REGISTRY: dict[str, Callable[[dict[str, Any]], dict[str, Any] | None]] = {}


def register_task(name: str):
    def decorator(func: Callable[[dict[str, Any]], dict[str, Any] | None]):
        TASK_REGISTRY[name] = func
        return func

    return decorator


def get_task(name: str) -> Callable[[dict[str, Any]], dict[str, Any] | None] | None:
    return TASK_REGISTRY.get(name)
