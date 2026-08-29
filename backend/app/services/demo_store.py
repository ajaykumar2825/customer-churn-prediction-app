"""In-memory demo dataset for zero-infrastructure operation.

When ``DATABASE_URL`` is not configured the API falls back to this store,
which is generated on first use by running the deployed model over the real
telco dataset. All dashboard endpoints therefore work out of the box.
"""

from __future__ import annotations

import functools

import numpy as np
import pandas as pd

from app.core import bootstrap  # noqa: F401  (ensures repo importability)

bootstrap.ensure_repo_importable()

from ml_pipeline.features import prepare  # noqa: E402


@functools.lru_cache(maxsize=1)
def _build_frame() -> pd.DataFrame:
    from ml_pipeline.config import DEFAULT_RAW_DATA

    from app.services.model_service import model_service

    frame = prepare(str(DEFAULT_RAW_DATA))
    df = frame[frame.columns.drop(["customer_id", "churn"])]
    probability = model_service._require("pipeline").predict_proba(df)[:, 1]
    frame["churn_probability"] = np.round(probability, 4)
    frame["predicted_churn"] = frame["churn_probability"] >= model_service.threshold_value()
    frame["satisfaction_score"] = _satisfaction(frame)
    frame["created_at"] = frame["tenure"].apply(_fake_created_at)
    return frame


def _satisfaction(frame: pd.DataFrame) -> np.ndarray:
    """Deterministic engagement/satisfaction score bound to [1, 5]."""
    raw = (
        2.1
        + 0.05 * np.minimum(frame["tenure"].to_numpy(), 72) / 72 * 3
        + 0.7 * frame["tech_support"].to_numpy()
        + 0.5 * frame["online_security"].to_numpy()
        + 0.4 * frame["dependents"].to_numpy()
        - 1.2 * (frame["churn_probability"].to_numpy() >= 0.7)
        - 0.5 * frame["multi_line"].to_numpy() * (frame["churn_probability"].to_numpy() >= 0.5)
    )
    return np.clip(raw, 1.0, 5.0).round(2)


def _fake_created_at(tenure: int) -> str:
    import datetime as dt

    return (dt.date.today() - dt.timedelta(days=int(tenure) + 14)).isoformat()


def get_frame() -> pd.DataFrame:
    return _build_frame()


def get_columns() -> list[str]:
    return list(get_frame().columns)


def search_customers(
    query: str | None = None,
    contract: str | None = None,
    risk: str | None = None,
    churn: bool | None = None,
    sort_by: str = "churn_probability",
    ascending: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    """Filter + paginate the demo store exactly like the DB-backed path."""
    frame = get_frame()
    mask = pd.Series(True, index=frame.index)
    if query:
        mask &= frame["customer_id"].str.contains(query, case=False, na=False)
    if contract:
        mask &= frame["contract"] == contract
    if risk:
        mask &= frame.apply(lambda r: _risk(r["churn_probability"]) == risk, axis=1)
    if churn is not None:
        mask &= frame["predicted_churn"] == churn
    filtered = frame[mask]
    total = int(len(filtered))
    if sort_by in filtered.columns:
        filtered = filtered.sort_values(sort_by, ascending=ascending)
    start = (page - 1) * page_size
    slice_ = filtered.iloc[start : start + page_size]
    records = [row_to_customer(row) for _, row in slice_.iterrows()]
    pages = max(int(np.ceil(total / page_size)), 1)
    return records, pages


def row_to_customer(row: pd.Series) -> dict:
    return {
        "customer_id": str(row["customer_id"]),
        "tenure": int(row["tenure"]),
        "monthly_charges": float(row["monthly_charges"]),
        "total_charges": float(row["total_charges"]),
        "avg_monthly_charge": float(row["avg_monthly_charge"]),
        "contract": str(row["contract"]),
        "internet_service": str(row["internet_service"]),
        "payment_method": str(row["payment_method"]),
        "senior_citizen": bool(row["senior_citizen"]),
        "gender_female": bool(row["gender_female"]),
        "partner": bool(row["partner"]),
        "dependents": bool(row["dependents"]),
        "paperless_billing": bool(row["paperless_billing"]),
        "multi_line": bool(row["multi_line"]),
        "online_security": bool(row["online_security"]),
        "online_backup": bool(row["online_backup"]),
        "device_protection": bool(row["device_protection"]),
        "tech_support": bool(row["tech_support"]),
        "streaming_tv": bool(row["streaming_tv"]),
        "streaming_movies": bool(row["streaming_movies"]),
        "total_services": int(row["total_services"]),
        "churn_probability": float(row["churn_probability"]),
        "risk_level": _risk(row["churn_probability"]),
        "predicted_churn": bool(row["predicted_churn"]),
        "observed_churn": bool(row["churn"]),
        "satisfaction_score": float(row["satisfaction_score"]),
        "created_at": str(row["created_at"]),
    }


def get_customer(customer_id: str) -> dict | None:
    frame = get_frame()
    row = frame[frame["customer_id"] == customer_id]
    if row.empty:
        return None
    return row_to_customer(row.iloc[0])


def _risk(probability: float) -> str:
    if probability >= 0.7:
        return "high"
    if probability >= 0.5:
        return "medium"
    return "low"
