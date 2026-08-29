"""Pydantic request/response models for prediction endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class PredictionInput(BaseModel):
    """The payload accepted by ``POST /predict``.

    Field names mirror the engineered features produced by the ML pipeline.
    """

    customer_id: str = Field(..., description="Business identifier of the customer.")
    tenure: int = Field(0, ge=0, le=360)
    monthly_charges: float = Field(0.0, ge=0, le=5000)
    total_charges: float = Field(0.0, ge=0, le=500_000)
    avg_monthly_charge: float = Field(0.0, ge=0, le=5000)
    senior_citizen: bool = False
    gender_female: bool = False
    paperless_billing: bool = False
    partner: bool = False
    dependents: bool = False
    multi_line: bool = False
    online_security: bool = False
    online_backup: bool = False
    device_protection: bool = False
    tech_support: bool = False
    streaming_tv: bool = False
    streaming_movies: bool = False
    total_services: int = Field(0, ge=0, le=12)
    internet_service: str = Field("Fiber optic")
    contract: str = Field("Month-to-month")
    payment_method: str = Field("Electronic check")

    @field_validator("internet_service", "contract", "payment_method")
    @classmethod
    def non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("avg_monthly_charge")
    @classmethod
    def derive_average(cls, value: float, info):
        """Auto-derive the average charge when it is left at its default."""

        if info.data.get("total_charges", 0) and info.data.get("tenure"):
            tenure = info.data["tenure"]
            if tenure > 0:
                return round(info.data["total_charges"] / tenure, 2)
        return value


class PredictionResponse(BaseModel):
    """Structured result of a single prediction."""

    customer_id: str
    probability: float = Field(..., ge=0, le=1)
    risk_level: str
    predicted_churn: bool
    confidence: float = Field(..., ge=0, le=1)
    threshold: float
    model: str
    model_version: str
    revenue_at_risk_monthly: float = 0.0
    retention_recommendation: str | None = None
    top_factors: list[dict[str, Any]] = Field(default_factory=list)
    explanation: dict[str, Any] | None = None


class BatchPredictionInput(BaseModel):
    """Columns-first batch payload validated against the feature contract."""

    customers: list[PredictionInput] = Field(..., min_length=1, max_length=10_000)


class BatchPredictionResponse(BaseModel):
    predictions: list[PredictionResponse]
    summary: dict[str, Any]
