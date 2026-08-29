"""Global configuration and paths for the churn ML pipeline.

Kept deliberately dependency-free so it can be imported from anywhere inside
the repository without pulling heavy scientific packages.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repository root -----------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]

# Canonical dataset location
DEFAULT_RAW_DATA = REPO_ROOT / "data" / "telco_churn.csv"

# Where every trained artifact is persisted
DEFAULT_MODEL_DIR = REPO_ROOT / "models"

# Human-consumable outputs
DEFAULT_REPORT_DIR = REPO_ROOT / "reports"

# SHAP artefacts live under models/shap
DEFAULT_SHAP_DIR: Path = DEFAULT_MODEL_DIR / "shap"

# -------------------------------------------------------------------------------
# Raw dataset schema (telco_customer_churn.csv from IBM / Kaggle)
# -------------------------------------------------------------------------------
RAW_COLUMNS: list[str] = [
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn",
]

TARGET = "churn"

# -------------------------------------------------------------------------------
# Engineered modelling schema used by the API and the frontend.
# These names are the public contract of the platform.
# -------------------------------------------------------------------------------
# Numeric / boolean (0/1) features, standardised at inference time.
NUMERIC_FEATURES: list[str] = [
    "tenure",
    "monthly_charges",
    "total_charges",
    "avg_monthly_charge",
    "senior_citizen",
    "gender_female",
    "paperless_billing",
    "partner",
    "dependents",
    "multi_line",
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
    "total_services",
]

# Categorical features, one-hot encoded with unknown-category handling.
CATEGORIC_FEATURES: list[str] = [
    "internet_service",
    "contract",
    "payment_method",
]

FEATURE_COLUMNS: list[str] = NUMERIC_FEATURES + CATEGORIC_FEATURES

# Which features were derived (shown in the "feature catalogue")
DERIVED_FEATURES: list[str] = [
    "avg_monthly_charge",
    "total_services",
    "gender_female",
    "partner",
    "dependents",
    "multi_line",
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
]


def ensure_dirs() -> None:
    """Create every output directory used by the pipeline."""
    for path in (DEFAULT_MODEL_DIR, DEFAULT_SHAP_DIR, DEFAULT_REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)
        os.makedirs(path, exist_ok=True)