"""The ML feature contract used by prediction and explanation services.

Single source of truth for accepted values so the app can validate payloads,
render human-readable labels and persist ``feature_metadata.json``.
"""

from __future__ import annotations

ML_FEATURE_CATALOGUE: dict[str, dict] = {
    "tenure": {"label": "Tenure (months)", "kind": "int", "ge": 0, "le": 360},
    "monthly_charges": {"label": "Monthly charges", "kind": "number", "ge": 0},
    "total_charges": {"label": "Total charges", "kind": "number", "ge": 0},
    "avg_monthly_charge": {"label": "Average monthly charge", "kind": "number", "ge": 0},
    "senior_citizen": {"label": "Senior citizen", "kind": "bool"},
    "gender_female": {"label": "Gender (female)", "kind": "bool"},
    "paperless_billing": {"label": "Paperless billing", "kind": "bool"},
    "partner": {"label": "Has partner", "kind": "bool"},
    "dependents": {"label": "Has dependents", "kind": "bool"},
    "multi_line": {"label": "Multiple lines", "kind": "bool"},
    "online_security": {"label": "Online security", "kind": "bool"},
    "online_backup": {"label": "Online backup", "kind": "bool"},
    "device_protection": {"label": "Device protection", "kind": "bool"},
    "tech_support": {"label": "Tech support", "kind": "bool"},
    "streaming_tv": {"label": "Streaming TV", "kind": "bool"},
    "streaming_movies": {"label": "Streaming movies", "kind": "bool"},
    "total_services": {"label": "Total services", "kind": "int", "ge": 0, "le": 12},
    "internet_service": {
        "label": "Internet service",
        "kind": "enum",
        "options": ["DSL", "Fiber optic", "No"],
    },
    "contract": {
        "label": "Contract",
        "kind": "enum",
        "options": ["Month-to-month", "One year", "Two year"],
    },
    "payment_method": {
        "label": "Payment method",
        "kind": "enum",
        "options": [
            "Electronic check",
            "Mailed check",
            "Bank transfer (automatic)",
            "Credit card (automatic)",
        ],
    },
}

BOOL_FEATURES: list[str] = [name for name, spec in ML_FEATURE_CATALOGUE.items() if spec["kind"] == "bool"]
ENUM_FEATURES: list[str] = [name for name, spec in ML_FEATURE_CATALOGUE.items() if spec["kind"] == "enum"]
NUMERIC_FEATURES: list[str] = [name for name, spec in ML_FEATURE_CATALOGUE.items() if spec["kind"] in {"int", "number"}]

FEATURE_ORDER: list[str] = list(ML_FEATURE_CATALOGUE.keys())

RISK_LABELS = {"low": "Low risk", "medium": "Medium risk", "high": "High risk"}