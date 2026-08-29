"""Raw data loading, cleaning and feature engineering.

The module turns the raw telecom CSV into the engineered modelling frame whose
column names are the public API contract shared with the FastAPI backend.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ml_pipeline.config import (
    CATEGORIC_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    TARGET,
)

_YES_NO_SET = {"Yes", "No"}

# Service add-ons expressed as Yes/No/No-phone-service/No-internet-service
_SERVICE_COLUMNS = {
    "multiplelines": "multi_line",
    "onlinesecurity": "online_security",
    "onlinebackup": "online_backup",
    "deviceprotection": "device_protection",
    "techsupport": "tech_support",
    "streamingtv": "streaming_tv",
    "streamingmovies": "streaming_movies",
}


def load_raw(path: str | pd.DirLike) -> pd.DataFrame:
    """Read the telco CSV and tidy column names (lowercase)."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce dtypes and drop rows with unusable values.

    - ``total_charges`` arrives as strings in the Telco dataset with blank
      cells; mislabeled blank cells are dropped when they carry no tenure.
    - ``churn`` is mapped to binary int.
    """
    df = df.copy()
    df["totalcharges"] = pd.to_numeric(df["totalcharges"], errors="coerce")
    df = df.dropna(subset=["totalcharges"]).reset_index(drop=True)
    df.loc[df["tenure"] == 0] = 0  # keep
    df[TARGET] = (df["churn"].map({"Yes": 1, "No": 0})).astype(int)
    df["tenure"] = df["tenure"].astype(int)
    df["monthlycharges"] = df["monthlycharges"].astype(float)
    return df


def _flag_yes(row: pd.Series, raw: str) -> int:
    """Encode ``Yes``/``No``/``No phone service``/``No internet service``."""
    value = str(row[raw]).strip().lower()
    return 1 if value == "yes" else 0


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    """Produce the modelling frame.

    Every returned column is one of ``FEATURE_COLUMNS`` plus an id and the
    target, so the backend can naively trust the column names.
    """
    df = df.copy()

    out = pd.DataFrame(index=df.index)
    out["customer_id"] = df["customerid"].astype(str)

    # --- derived / binary features -------------------------------------------
    out["gender_female"] = (df["gender"].str.lower() == "female").astype(int)
    out["senior_citizen"] = df["seniorcitizen"].astype(int)
    out["paperless_billing"] = (df["paperlessbilling"].str.lower() == "yes").astype(int)
    out["partner"] = (df["partner"].str.lower() == "yes").astype(int)
    out["dependents"] = (df["dependents"].str.lower() == "yes").astype(int)

    for raw, engineered in _SERVICE_COLUMNS.items():
        out[engineered] = df.apply(lambda r, rw=raw: _flag_yes(r, rw), axis=1)

    # --- directly passthrough numeric features --------------------------------
    out["tenure"] = df["tenure"].astype(int)
    out["monthly_charges"] = df["monthlycharges"].astype(float)
    out["total_charges"] = df["totalcharges"].astype(float)

    # --- derived numeric features ----------------------------------------------
    tenure = np.where(df["tenure"] > 0, df["tenure"], 1)
    out["avg_monthly_charge"] = (df["totalcharges"] / tenure).round(2)
    out["total_services"] = out[list(_SERVICE_COLUMNS.values())].sum(axis=1).astype(int)

    # --- categorical features ---------------------------------------------------
    out["internet_service"] = df["internetservice"].astype(str)
    out["contract"] = df["contract"].astype(str)
    out["payment_method"] = df["paymentmethod"].astype(str)

    # --- target ----------------------------------------------------------------
    out[TARGET] = df[TARGET].astype(int)

    return out[["customer_id", *FEATURE_COLUMNS, TARGET]]


def prepare(path: str) -> pd.DataFrame:
    """Convenience pipe: load -> clean -> engineer."""
    return engineer(clean(load_raw(path)))