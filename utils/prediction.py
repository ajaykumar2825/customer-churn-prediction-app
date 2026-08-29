"""Prediction utilities shared by the single/batch scoring flows."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from utils.preprocessing import engineered_for_prediction, risk_band


def score_frame(pipeline, frame: pd.DataFrame) -> pd.DataFrame:
    """Attach ``churn_probability`` (and bucket) to an engineered frame."""
    out = frame.copy()
    X = engineered_for_prediction(out)
    proba = pipeline.predict_proba(X)[:, 1]
    out["churn_probability"] = np.asarray(proba, dtype=float)
    out["risk"] = out["churn_probability"].map(risk_band)
    return out


def score_single(pipeline, frame: pd.DataFrame) -> dict[str, Any]:
    """Score a one-row engineered frame into a rich result dict."""
    scored = score_frame(pipeline, frame).iloc[0]
    return {
        "customer_id": str(scored["customer_id"]),
        "probability": float(scored["churn_probability"]),
        "risk": str(scored["risk"]),
        "monthly_charges": float(scored["monthly_charges"]),
        "contract": str(scored["contract"]),
    }


def batch_summary(scored: pd.DataFrame, threshold: float) -> dict[str, Any]:
    """Roll-up KPIs for a scored batch, honouring the operational threshold."""
    p = scored["churn_probability"].to_numpy()
    monthly = scored["monthly_charges"].to_numpy(dtype=float)
    flagged = scored["churn_probability"] >= threshold
    return {
        "rows": int(len(scored)),
        "expected_churners": int((flagged).sum()),
        "mean_probability": float(p.mean()),
        "high_risk": int((p >= 0.7).sum()),
        "medium_risk": int(((p >= 0.5) & (p < 0.7)).sum()),
        "low_risk": int((p < 0.5).sum()),
        "expected_monthly_loss": float((monthly * p).sum()),
        "expected_annual_loss": float((monthly * p).sum() * 12),
        "threshold": float(threshold),
    }