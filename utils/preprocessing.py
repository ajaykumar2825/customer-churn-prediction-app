"""Preprocessing: build the engineered modelling frame from user input."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ml_pipeline.config import (
    CATEGORIC_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    TARGET,
)
from ml_pipeline.feature_catalogue import ML_FEATURE_CATALOGUE

# Defaults mirroring the demo customer so a bare batch row still scores safely.
DEFAULT_INPUT: dict = {
    "customer_id": "DEMO-0001",
    "tenure": 24,
    "monthly_charges": 79.99,
    "total_charges": 1919.76,
    "avg_monthly_charge": 79.99,
    "senior_citizen": False,
    "gender_female": True,
    "paperless_billing": True,
    "partner": False,
    "dependents": False,
    "multi_line": True,
    "online_security": False,
    "online_backup": False,
    "device_protection": True,
    "tech_support": False,
    "streaming_tv": True,
    "streaming_movies": False,
    "total_services": 5,
    "internet_service": "Fiber optic",
    "contract": "Month-to-month",
    "payment_method": "Electronic check",
}


def _coerce_value(name: str, value, catalogue: dict) -> Any:
    spec = catalogue.get(name, {})
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if name in ML_FEATURE_CATALOGUE and ML_FEATURE_CATALOGUE[name]["kind"] == "bool":
        if isinstance(value, str):
            return value.strip().lower() in {"yes", "true", "1", "y"}
        return bool(value)
    if name in {"internet_service", "contract", "payment_method"}:
        return str(value).strip()
    return value


def rows_to_engineered(rows: list[dict]) -> pd.DataFrame:
    """Normalise a list of raw input dicts into the modelling frame.

    Every missing field falls back to ``DEFAULT_INPUT`` so partial rows from
    batch uploads still produce a valid engineered row.
    """
    catalogue = ML_FEATURE_CATALOGUE
    records: list[dict] = []
    for raw in rows:
        merged = {**DEFAULT_INPUT, **{k: v for k, v in raw.items() if v is not None}}
        record: dict = {}
        for name in [*NUMERIC_FEATURES, *CATEGORIC_FEATURES]:
            value = _coerce_value(name, merged.get(name), catalogue)
            if value is None:
                value = DEFAULT_INPUT[name]
            record[name] = value
        record["customer_id"] = str(merged.get("customer_id") or DEFAULT_INPUT["customer_id"])
        records.append(record)

    frame = pd.DataFrame(records)
    frame["customer_id"] = frame["customer_id"].astype(str)
    # Guarantee dtype parity with the trained frame.
    for name in NUMERIC_FEATURES:
        frame[name] = pd.to_numeric(frame[name], errors="coerce").fillna(0.0)
    frame["total_services"] = frame["total_services"].astype(int)
    frame["tenure"] = frame["tenure"].astype(int)
    return frame[["customer_id", *FEATURE_COLUMNS]]


def engineered_for_prediction(frame: pd.DataFrame) -> pd.DataFrame:
    """Model input minus the id column, columns ordered as trained."""
    return frame[FEATURE_COLUMNS]


def risk_band(probability: float) -> str:
    """Map a probability onto the platform risk vocabulary."""
    if probability >= 0.7:
        return "high"
    if probability >= 0.5:
        return "medium"
    return "low"


def parse_jsonl(text: str) -> list[dict]:
    """Parse one JSON object per line (or a bare JSON array)."""
    import json

    rows: list[dict] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if isinstance(json.loads(line), dict):
            rows.append(json.loads(line))
    return rows


def coerce_uploaded_to_engineered(uploaded_df: pd.DataFrame) -> pd.DataFrame:
    """Accept either the engineered 20-feature schema or a raw Telco CSV."""
    import numpy as np

    from ml_pipeline.features import clean, engineer

    upper_cols = {str(c).strip().lower(): c for c in uploaded_df.columns}
    has_raw = any(k in upper_cols for k in ["customerid", "seniorcitizen", "churn", "phone service"])
    used_id = has_raw or "customer_id" not in upper_cols

    if has_raw:
        raw = uploaded_df.rename(columns=upper_cols)
        if "churn" not in raw.columns:
            raw["churn"] = np.nan
        engineered = engineer(clean(raw))
        engineered = engineered.drop(columns=["churn"], errors="ignore")
        if not used_id:
            engineered["customer_id"] = uploaded_df["customer_id"].astype(str).values
        return engineered.reindex(columns=["customer_id", *FEATURE_COLUMNS])

    records = uploaded_df.rename(columns=upper_cols).to_dict("records")
    return rows_to_engineered(records)