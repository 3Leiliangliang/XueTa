from __future__ import annotations

import time
from typing import Any

from app.tasks.registry import register_task


@register_task("demo.echo")
def demo_echo(payload: dict[str, Any]) -> dict[str, Any]:
    return {"echo": payload}


@register_task("demo.sleep")
def demo_sleep(payload: dict[str, Any]) -> dict[str, Any]:
    seconds = float(payload.get("seconds", 1))
    seconds = max(0.0, min(seconds, 30.0))
    time.sleep(seconds)
    return {"slept": seconds}
