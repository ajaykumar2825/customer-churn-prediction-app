"""TTL cache with an automatic Redis backend and in-memory fallback.

The in-memory backend is a plain dict with expiry checks, which keeps the app
functional without any infrastructure while remaining production-ready when
``REDIS_URL`` is supplied.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections.abc import Callable
from typing import Any

from app.core.config import settings

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None  # type: ignore

logger_import_error: list[str] = []


class Cache:
    """Simple namespaced TTL cache."""

    def __init__(self, namespace: str = "churn") -> None:
        self.namespace = namespace
        self._memory: dict[str, tuple[float, str]] = {}
        self._lock = threading.Lock()
        self._redis = self._connect_redis()

    def _connect_redis(self):
        if redis is None or not settings.redis_url:
            return None
        try:
            client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            return client
        except Exception:
            return None

    def _key(self, key: str) -> str:
        digest = hashlib.sha256(key.encode()).hexdigest()
        return f"{self.namespace}:{digest}"

    def get_json(self, key: str) -> Any:
        """Return a cached JSON document or ``None``."""
        cache_key = self._key(key)
        if self._redis is not None:
            try:
                raw = self._redis.get(cache_key)
                return json.loads(raw) if raw else None
            except Exception:
                return None
        with self._lock:
            entry = self._memory.get(cache_key)
            if entry is None:
                return None
            expires_at, raw = entry
            if expires_at < time.monotonic():
                self._memory.pop(cache_key, None)
                return None
            return json.loads(raw) if raw else None

    def set_json(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        cache_key = self._key(key)
        ttl = ttl_seconds or settings.cache_ttl_seconds
        try:
            raw = json.dumps(value, default=str)
        except (TypeError, ValueError):
            return
        if self._redis is not None:
            try:
                self._redis.setex(cache_key, ttl, raw)
                return
            except Exception:
                pass
        with self._lock:
            self._memory[cache_key] = (time.monotonic() + ttl, raw)

    def cached(self, ttl_seconds: int | None = None) -> Callable:
        """Decorator caching a JSON-serialisable function result by argument hash."""

        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **_kwargs):
                tag = hashlib.sha256(repr(args).encode()).hexdigest()[:16]
                key = f"{func.__name__}:{tag}"
                hit = self.get_json(key)
                if hit is not None:
                    return hit
                result = func(*args, **_kwargs)
                self.set_json(key, result, ttl_seconds)
                return result

            return wrapper

        return decorator

    @property
    def backend(self) -> str:
        return "redis" if self._redis is not None else "memory"


cache = Cache()
