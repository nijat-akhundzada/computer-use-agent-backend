import json
from typing import Any

from app.core.redis import get_redis

QUEUE_KEY = "jobs:agent"


def enqueue(job: dict[str, Any]) -> None:
    r = get_redis()
    r.lpush(QUEUE_KEY, json.dumps(job))


def dequeue_blocking(timeout_seconds: int = 5) -> dict[str, Any] | None:
    """
    BRPOP blocks until an item is available or timeout.
    Returns job dict or None.
    """
    r = get_redis()
    item = r.brpop(QUEUE_KEY, timeout=timeout_seconds)
    if not item:
        return None
    _, payload = item
    return json.loads(payload)
