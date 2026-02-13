from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

_store: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def rate_limit(rule: str, *, limit: int, window_seconds: int):
    def dependency(request: Request) -> None:
        key = (rule, _client_key(request))
        now = time.time()
        window_start = now - window_seconds

        with _lock:
            queue = _store[key]
            while queue and queue[0] < window_start:
                queue.popleft()

            if len(queue) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for {rule}",
                )
            queue.append(now)

    return dependency


def reset_rate_limits() -> None:
    with _lock:
        _store.clear()
