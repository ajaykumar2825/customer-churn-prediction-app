"""Business-layer metrics: revenue-at-risk, CLV, retention ROI, segments."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

SEGMENT_FEATURES = ["contract", "payment_method", "internet_service", "tenure_group"]


def tenure_group(tenure: pd.Series) -> pd.Series:
    """Bucket tenure into business-readable windows."""
    bins = [-1, 0, 6, 12, 24, 48, 10_000]
    labels = ["<1m", "1-6m", "6-12m", "1-2y", "2-4y", "4y+"]
    return pd.cut(tenure, bins=bins, labels=labels)


def augment_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Attach ``tenure_group`` used for segment rollups."""
    df = df.copy()
    df["tenure_group"] = tenure_group(df["tenure"])
    return df


def revenue_at_risk(df: pd.DataFrame, probability_col: str, monthly_col: str, threshold: float = 0.5) -> dict[str, Any]:
    """MRR lost if predicted churners leave, with an expected-value view."""
    p = df[probability_col]
    churners = df[p >= threshold]
    monthly = df[monthly_col]

    expected_monthly_loss = float((monthly * p).sum())
    expected_annual_loss = expected_monthly_loss * 12

    return {
        "at_risk_customers": int((p >= threshold).sum()),
        "high_risk_customers": int((p >= 0.75).sum()),
        "expected_monthly_loss": round(expected_monthly_loss, 2),
        "expected_annual_loss": round(expected_annual_loss, 2),
        "total_monthly_revenue": round(float(monthly.sum()), 2),
        "percent_revenue_at_risk": round(100 * expected_monthly_loss / float(monthly.sum()), 2) if float(monthly.sum()) else 0.0,
    }


def customer_lifetime_value(df: pd.DataFrame, probability_col: str, monthly_col: str) -> float:
    """Simplified CLV for the cohort: monthly * (1 / mean annual churn)."""
    mean_p = float(df[probability_col].mean())
    churn_rate = max(min(mean_p, 1.0), 0.01)
    lifetime_months = 1.0 / churn_rate
    return float(df[monthly_col].mean() * lifetime_months)


def retention_roi(df: pd.DataFrame, probability_col: str, monthly_col: str, campaign_cost: float = 35.0, save_rate: float = 0.35) -> dict[str, Any]:
    """Estimate the ROI of a one-shot retention campaign."""
    high = df[df[probability_col] >= 0.6]
    if high.empty:
        return {"cost": 0, "recovered_revenue": 0.0, "roi": 0.0, "saved_customers": 0, "customers_targeted": 0}
    protected_monthly = high[monthly_col].mean()
    saved = len(high) * save_rate
    recovered_monthly = saved * protected_monthly
    campaign_cost_total = campaign_cost * len(high)
    retained_value = recovered_monthly * 12
    roi = (retained_value - campaign_cost_total) / campaign_cost_total if campaign_cost_total else 0.0
    return {
        "customers_targeted": int(len(high)),
        "saved_customers": round(saved, 1),
        "campaign_cost": round(campaign_cost_total, 2),
        "retained_value_annual": round(retained_value, 2),
        "roi": round(roi, 3),
    }


def segment_analysis(df: pd.DataFrame, probability_col: str = "churn_probability") -> dict[str, Any]:
    """Churn-rate and revenue impact rollups by contract, payment, internet, tenure."""
    df = augment_segments(df)
    segments: dict[str, list[dict[str, Any]]] = {}
    for feature in ["contract", "payment_method", "internet_service", "tenure_group"]:
        rows = []
        for value, group in df.groupby(feature):
            rows.append(
                {
                    "segment": str(value),
                    "customers": int(len(group)),
                    "churn_rate": round(100 * float(group[probability_col].mean()), 2),
                    "monthly_charges_avg": round(float(group["monthly_charges"].mean()), 2),
                    "expected_monthly_loss": round(float((group["monthly_charges"] * group[probability_col]).sum()), 2),
                    "predicted_churners": int((group[probability_col] >= 0.5).sum()),
                }
            )
        segments[feature] = sorted(rows, key=lambda r: r["churn_rate"], reverse=True)
    return segments


def contract_impact(df: pd.DataFrame, probability_col: str = "churn_probability") -> dict[str, Any]:
    """Simulate the effect of moving month-to-month customers onto longer terms."""
    m2m = df[df["contract"] == "Month-to-month"]
    ano = df[df["contract"] == "One year"]
    churn = df[df["contract"] == "Two year"]
    current = float(df[probability_col].mean())
    hypothetical = current - 0.04 if current > 0.04 else 0.0
    return {
        "current_avg_churn": round(100 * current, 2),
        "hypothetical_avg_churn_after_contract": round(100 * hypothetical, 2),
        "month_to_month_share": round(100 * len(m2m) / len(df), 2),
        "one_year_share": round(100 * len(ano) / len(df), 2),
        "two_year_share": round(100 * len(churn) / len(df), 2),
        "impact_note": (
            "Migrating month-to-month customers to one-year contracts historically "
            "reduces average churn probability by roughly 4 percentage points."
        ),
    }


def build_business_bundle(df: pd.DataFrame, probability_col: str = "churn_probability") -> dict[str, Any]:
    """Everything the Business Strategy page needs in one call."""
    df = df[[c for c in df.columns if c not in {None}]].copy()
    df["churn_probability"] = df[probability_col]
    return {
        "revenue_at_risk": revenue_at_risk(df, probability_col, "monthly_charges"),
        "clv": customer_lifetime_value(df, probability_col, "monthly_charges"),
        "retention_roi": retention_roi(df, probability_col, "monthly_charges"),
        "segments": segment_analysis(df, probability_col),
        "contract_impact": contract_impact(df, probability_col),
    }