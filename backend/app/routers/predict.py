"""Prediction endpoints: single, batch and full SHAP explanations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ModelNotReady, ValidationFailed
from app.ml_feature_catalogue import FEATURE_ORDER, ML_FEATURE_CATALOGUE
from app.schemas.prediction import (
    BatchPredictionInput,
    BatchPredictionResponse,
    PredictionInput,
    PredictionResponse,
)
from app.services.model_service import model_service
from app.services.seed_service import audit

router = APIRouter(tags=["prediction"])


@router.get("/feature-catalogue")
def feature_catalogue() -> dict:
    """The 20-feature contract the dashboard renders into a prediction form."""
    return {
        "catalogue": ML_FEATURE_CATALOGUE,
        "feature_order": FEATURE_ORDER,
    }


def _require_model() -> None:
    if not model_service.ready:
        raise ModelNotReady()


@router.post("/predict", response_model=PredictionResponse)
def predict(
    payload: PredictionInput,
    request: Request,
    session: Session = Depends(get_db),
    x_forwarded_for: str | None = Header(default=None),
) -> dict:
    """Score one customer and return risk, SHAP factors and recommendations."""
    _require_model()
    customer = payload.model_dump()
    result = model_service.predict(customer)
    audit(
        session,
        action="predict.created",
        resource=f"/predict/{customer['customer_id']}",
        detail=f"probability={result['probability']:.3f} risk={result['risk_level']}",
        ip=x_forwarded_for or (request.client.host if request.client else ""),
    )
    return result


@router.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(
    payload: BatchPredictionInput,
    session: Session = Depends(get_db),
    x_forwarded_for: str | None = Header(default=None),
) -> dict:
    """Score up to 10,000 customers in a single call."""
    _require_model()
    customers = [c.model_dump() for c in payload.customers]
    result = model_service.predict_batch(customers)
    audit(
        session,
        action="predict.batch",
        resource="/predict/batch",
        detail=f"rows={result['summary']['count']} expected_churners={result['summary']['expected_churners']}",
        ip=x_forwarded_for or "",
    )
    return result


@router.post("/explain")
def explain(payload: PredictionInput, request: Request) -> dict:
    """Local SHAP explanation for an arbitrary customer profile."""
    _require_model()
    customer = payload.model_dump()
    explanation = model_service.explain_input(customer)
    if explanation is None:
        raise ValidationFailed("Unable to produce an explanation for this profile.")
    probability = model_service.predict(customer)["probability"]
    return {
        "customer_id": customer["customer_id"],
        "probability": probability,
        "risk_level": "high" if probability >= settings.high_risk_threshold else "medium" if probability >= 0.5 else "low",
        "explanation": explanation,
    }
