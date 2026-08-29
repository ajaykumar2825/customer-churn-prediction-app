"""Health and readiness endpoints."""

from __future__ import annotations

import time

from fastapi import APIRouter

from app.core.cache import cache
from app.core.config import settings
from app.core.database import database_online
from app.services.model_service import model_service

router = APIRouter(tags=["system"])

_UP_AT = time.time()


@router.get("/health")
def health() -> dict:
    """Liveness probe."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "database": "connected" if database_online() else "degraded",
        "model": model_service.model_name() if model_service.ready else "not_loaded",
        "cache": cache.backend,
    }


@router.get("/ready")
def readiness() -> dict:
    """Readiness probe for orchestrators / load balancers."""
    return {"ready": model_service.ready, "model_loaded": model_service.ready, "database_online": database_online()}


@router.get("/ops/metrics")
def metrics() -> dict:
    """Operational counters (lightweight readiness payload)."""
    return {
        "model": {
            "loaded": model_service.ready,
            "name": model_service.model_name() if model_service.ready else "n/a",
        },
        "application": {"uptime_seconds": int(time.time() - _UP_AT), "latency_ms_header": "x-response-time"},
    }
