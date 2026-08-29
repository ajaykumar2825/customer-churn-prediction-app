"""Shared analytics aggregations over the scored customer base (cached)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from ml_pipeline.business import tenure_group
from utils.prediction import score_frame


@st.cache_resource(show_spinner="Scoring customer base…")
def scored_frame() -> pd.DataFrame:
    """Engineered frame + a live churn probability per customer."""
    from utils.loader import load_data, load_model_bundle

    base = load_data()
    bundle = load_model_bundle()
    return score_frame(bundle["pipeline"], base)


def tenure_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    """Per-cohort revenue and churn rollup for the overview charts."""
    frame = df.copy()
    frame["cohort"] = tenure_group(frame["tenure"]).astype(str)
    order = ["<1m", "1-6m", "6-12m", "1-2y", "2-4y", "4y+"]
    agg = (
        frame.groupby("cohort", observed=True)
        .agg(revenue=("monthly_charges", "sum"), churned=("churn", "sum"), customers=("customer_id", "count"))
        .reindex(order)
        .reset_index()
    )
    return agg


def risk_split(df: pd.DataFrame) -> dict[str, int]:
    p = df["churn_probability"]
    return {
        "Low risk": int((p < 0.5).sum()),
        "Medium risk": int(((p >= 0.5) & (p < 0.7)).sum()),
        "High risk": int((p >= 0.7).sum()),
    }


def exposure(df: pd.DataFrame, threshold: float = 0.5) -> dict[str, Any]:
    p = df["churn_probability"].to_numpy()
    monthly = df["monthly_charges"].to_numpy()
    flagged = p >= threshold
    expected_monthly = float((monthly * p).sum())
    return {
        "at_risk_customers": int(flagged.sum()),
        "high_risk": int((p >= 0.7).sum()),
        "expected_monthly_loss": expected_monthly,
        "expected_annual_loss": expected_monthly * 12,
        "total_monthly_revenue": float(monthly.sum()),
        "percent_at_risk": 100 * expected_monthly / float(monthly.sum()),
        "mean_probability": float(p.mean()),
        "threshold": float(threshold),
    }


def campaign_economics(df: pd.DataFrame, prob_col: str = "churn_probability") -> dict[str, Any]:
    """One-shot outreach campaign on p>=0.6 at $35/contact and a 35% save rate."""
    p = df[prob_col].to_numpy()
    monthly = df["monthly_charges"].to_numpy()
    high = p >= 0.6
    n_high = int(high.sum())
    if n_high == 0:
        return {"targeted": 0, "saved": 0, "cost": 0, "recovered_annual": 0, "roi": 0}
    saved = n_high * 0.35
    protected_monthly = monthly[high].mean()
    cost = n_high * 35.0
    recovered_annual = saved * protected_monthly * 12
    roi = (recovered_annual - cost) / cost if cost else 0
    return {
        "targeted": n_high,
        "saved": round(saved, 1),
        "cost": round(cost, 2),
        "recovered_annual": round(recovered_annual, 2),
        "roi": round(roi, 3),
    }


def segment_rollups(df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    """Churn-rate rollups for the four segmentation dimensions."""
    out: dict[str, list[dict[str, Any]]] = {}
    frame = df.copy()
    frame["cohort"] = tenure_group(frame["tenure"]).astype(str)
    for key in ["contract", "payment_method", "internet_service", "cohort"]:
        rows = []
        for value, group in frame.groupby(key, observed=True):
            p = group["churn_probability"]
            rows.append(
                {
                    "segment": str(value),
                    "customers": int(len(group)),
                    "churn_rate": round(100 * float(p.mean()), 2),
                    "predicted_churners": int((p >= 0.5).sum()),
                    "expected_monthly_loss": round(float((group["monthly_charges"] * p).sum()), 2),
                    "monthly_charges_avg": round(float(group["monthly_charges"].mean()), 2),
                }
            )
        out[key] = sorted(rows, key=lambda r: r["churn_rate"], reverse=True)
    return out


def watchlist(df: pd.DataFrame, top: int = 6) -> pd.DataFrame:
    return df.sort_values("churn_probability", ascending=False).head(top)


def permutation_importance_items(importance: dict) -> list[dict]:
    perm = importance.get("permutation") or []
    if isinstance(perm, dict) and "error" in perm:
        return []
    return perm if isinstance(perm, list) else [{"feature": "n/a", "importance": 0.0, "std": 0.0}]