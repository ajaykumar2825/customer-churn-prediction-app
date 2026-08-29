"""Analytics, model-performance and strategy endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.core.database import get_db
from app.schemas.analytics import AnalyticsResponse, ModelMetricsResponse
from app.services.customer_service import customer_service
from app.services.model_service import model_service

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(session: Session = Depends(get_db)) -> dict:
    """Full executive-dashboard payload (KPIs, trends, risk, recent)."""
    cached = cache.get_json("analytics:executive")
    if cached is not None:
        return cached
    payload = customer_service.analytics(session)
    cache.set_json("analytics:executive", payload, ttl_seconds=120)
    return payload


@router.get("/revenue-risk")
def revenue_risk(session: Session = Depends(get_db)) -> dict:
    """Business bundle: revenue at risk, CLV, retention ROI and segments."""
    cached = cache.get_json("analytics:revenue")
    if cached is not None:
        return cached
    bundle = customer_service.revenue_bundle(session)
    payload = {"bundle": bundle}
    cache.set_json("analytics:revenue", payload, ttl_seconds=300)
    return payload


@router.get("/segments")
def segments(session: Session = Depends(get_db)) -> dict:
    """Churn-rate and revenue rollups by contract, payment, internet, tenure."""
    bundle = customer_service.revenue_bundle(session)
    return {"segments": bundle.get("segments", {})}


@router.get("/metrics", response_model=ModelMetricsResponse)
def model_metrics() -> dict:
    """Model performance pack: leaderboard, curves, confusion, importance, meta."""
    return model_service.metrics_payload()


@router.get("/feature-importance")
def feature_importance() -> dict:
    """SHAP + permutation feature importances."""
    return {"importance": model_service.feature_importance()}


@router.get("/model/status")
def model_status() -> dict:
    """Champion model metadata and serving health."""
    payload = model_service.metrics_payload()
    return {
        "model": payload["meta"],
        "metrics": payload["metrics"],
        "threshold": payload["threshold"],
        "ready": model_service.ready,
    }
