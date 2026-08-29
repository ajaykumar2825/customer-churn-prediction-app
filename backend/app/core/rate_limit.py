"""Sliding-window rate limiter with Redis or in-memory backends.

The limiter keys on ``(client_ip, route)``; a middleware attached to the app
enforces it. The in-memory implementation is only correct when the process is
single-instance, which the compose deployment (a single FastAPI container)
satisfies — with redis configured it becomes multi-instance safe.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.cache import cache
from app.core.config import settings


class SlidingWindowLimiter:
    """Token/sliding-window limiter per (identifier, bucket)."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: defaultdict[str, deque] = defaultdict(deque)

    def _key(self, identifier: str, bucket: str) -> str:
        return f"ratelimit:{identifier}:{bucket}"

    def allow(self, identifier: str, bucket: str = "default") -> bool:
        key = self._key(identifier, bucket)
        if cache.backend == "redis":
            now = int(time.time())
            try:
                raw = cache._redis.zremrangebyscore(key, 0, now - self.window_seconds)  # type: ignore[union-attr]
                del raw
                count = cache._redis.zcard(key)  # type: ignore[union-attr]
                if count >= self.max_requests:
                    return False
                cache._redis.zadd(key, {f"{now}-{count}": now})  # type: ignore[union-attr]
                cache._redis.expire(key, self.window_seconds)  # type: ignore[union-attr]
                return True
            except Exception:
                return True
        now = time.monotonic()
        history = self._history[key]
        while history and history[0] <= now - self.window_seconds:
            history.popleft()
        if len(history) >= self.max_requests:
            return False
        history.append(now)
        return True

    def client_identifier(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


limiter = SlidingWindowLimiter(settings.rate_limit_requests, settings.rate_limit_window_seconds)


async def rate_limit_middleware(request: Request, call_next):
    """Enforce limits on sensitive write/predict routes."""
    path = request.url.path
    protected = any(path.endswith(p) for p in ("/predict", "/predict/batch", "/explain"))
    if protected:
        identifier = limiter.client_identifier(request)
        if not limiter.allow(identifier, bucket=path):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "ok": False,
                    "error": {
                        "code": "rate_limited",
                        "message": f"Rate limit exceeded: {limiter.max_requests} requests per "
                        f"{limiter.window_seconds}s.",
                    },
                },
            )
    return await call_next(request)
