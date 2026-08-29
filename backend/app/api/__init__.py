"""API router aggregation under the versioned prefix."""

from __future__ import annotations

from fastapi import APIRouter

from app.routers import analytics, customers, health, predict

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(customers.router)
api_router.include_router(predict.router)
api_router.include_router(analytics.router)
