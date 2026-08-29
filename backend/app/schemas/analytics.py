"""Pydantic models for customer and analytics endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CustomerOut(BaseModel):
    """Public customer record with predicted churn state."""

    customer_id: str
    tenure: int
    monthly_charges: float
    total_charges: float
    avg_monthly_charge: float
    contract: str
    internet_service: str
    payment_method: str
    senior_citizen: bool
    gender_female: bool
    partner: bool
    dependents: bool
    paperless_billing: bool
    total_services: int
    churn_probability: float
    risk_level: str
    predicted_churn: bool
    observed_churn: bool = False
    created_at: str | None = None


class CustomersPage(BaseModel):
    items: list[CustomerOut]
    total: int
    page: int
    page_size: int
    pages: int


class AnalyticsResponse(BaseModel):
    """Executive dashboard payload."""

    kpis: dict[str, Any]
    trends: dict[str, list[Any]]
    risk_distribution: list[dict[str, Any]]
    recent_predictions: list[dict[str, Any]]
    quick_stats: dict[str, Any]


class RevenueRiskResponse(BaseModel):
    bundle: dict[str, Any]


class ModelMetricsResponse(BaseModel):
    meta: dict[str, Any]
    leaderboard: list[dict[str, Any]]
    threshold: dict[str, Any]
    metrics: dict[str, Any]
    curves: dict[str, Any]
    confusion: dict[str, Any]
    importance: dict[str, Any]
