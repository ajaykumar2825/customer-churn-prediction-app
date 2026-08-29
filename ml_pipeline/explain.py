"""SHAP explainability: global summary, local explanations, plots, NL text.

The backend re-uses :func:`explain_local` for single-row explanations and the
precomputed global artefacts for the Explainability page.
"""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd

from ml_pipeline.config import DEFAULT_MODEL_DIR, DEFAULT_SHAP_DIR

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import shap
except Exception:  # pragma: no cover - optional
    shap = None  # type: ignore
    plt = None  # type: ignore


def compute_global_explanations(model, preprocessor, X_sample: np.ndarray, feature_names: list[str]) -> dict[str, Any]:
    """Explainer over a (transformed) sample; returns global artefacts."""
    if shap is None:
        return {"error": "shap is not installed"}

    explainer = _explainer_for(model, X_sample)
    shap_values = explainer.shap_values(X_sample)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    expected = _expected_value(explainer)

    mean_abs = np.abs(shap_values).mean(axis=0)
    importances = [
        {"feature": name, "importance": float(value)}
        for name, value in sorted(zip(feature_names, mean_abs), key=lambda kv: kv[1], reverse=True)
    ]

    payload = {
        "expected_value": expected,
        "n_rows": int(X_sample.shape[0]),
        "importances": importances[:50],
    }

    if plt is not None:
        # Summary (beeswarm) plot -----------------------------------------
        fig, ax = plt.subplots(figsize=(12, 9))
        shap.summary_plot(shap_values, X_sample, feature_names=feature_names, show=False)
        plt.tight_layout()
        fig.savefig(DEFAULT_SHAP_DIR / "shap_summary_beeswarm.png", dpi=120, bbox_inches="tight")
        plt.close(fig)

        # Bar summary --------------------------------------------------------
        fig, ax = plt.subplots(figsize=(10, 6))
        shap.summary_plot(shap_values, X_sample, feature_names=feature_names, plot_type="bar", show=False)
        plt.tight_layout()
        fig.savefig(DEFAULT_SHAP_DIR / "shap_summary_bar.png", dpi=120, bbox_inches="tight")
        plt.close(fig)

    return payload


def _expected_value(explainer) -> float:
    ev = explainer.expected_value
    if isinstance(ev, (list, tuple, np.ndarray)):
        values = np.asarray(ev, dtype="float64")
        return float(values.mean())
    if getattr(explainer, "model_output", None) == "probability":
        return float(ev)
    return float(ev)


def _explainer_for(model, X_sample: np.ndarray | None = None):
    """Pick an efficient explainer based on the fitted model type."""
    if shap is None:  # pragma: no cover
        raise RuntimeError("shap is required")
    model_type = type(model).__name__
    linear_types = ("LogisticRegression", "LinearSVC", "RidgeClassifier", "SGDClassifier")
    if model_type in linear_types:
        return shap.LinearExplainer(model, np.asarray(X_sample) if X_sample is not None else None)
    if hasattr(model, "get_booster") or hasattr(model, "_Booster") or model_type.startswith(("CatBoost", "XGB", "LGBM")):
        return shap.TreeExplainer(model)
    if X_sample is not None and hasattr(model, "predict_proba"):
        try:
            return shap.TreeExplainer(model)
        except Exception:
            return shap.KernelExplainer(model.predict_proba, np.asarray(X_sample)[:50])
    raise RuntimeError(f"No explainer available for {model_type}")


def explain_local(model, preprocessor, X_input: np.ndarray, encoded_names: list[str]) -> dict[str, Any]:
    """SHAP values for a single transformed row + NL-friendly description."""
    if shap is None:  # pragma: no cover
        raise RuntimeError("shap is required")
    explainer = _explainer_for(model, X_input)
    sv = explainer.shap_values(X_input)
    if isinstance(sv, list):
        sv = sv[1]
    base = float(np.array(explainer.expected_value).mean())
    values = np.asarray(sv).ravel()
    items = sorted(zip(encoded_names, values), key=lambda kv: abs(kv[1]), reverse=True)
    return {
        "base_value": round(base, 4),
        "prediction": None,  # filled by caller
        "contributions": [
            {"feature": name, "value": round(float(v), 4)}
            for name, v in items
        ],
    }


def natural_language_explanation(
    contributions: list[dict[str, Any]],
    feature_values: dict[str, Any],
    threshold: float,
    churn_probability: float,
) -> dict[str, str]:
    """Turn top SHAP contributions into plain-English insight sentences."""
    risk = "high risk" if churn_probability >= threshold else "moderate" if churn_probability >= threshold * 0.6 else "low risk"
    lines = [f"Customer is classified as **{risk}** of churning with {churn_probability:.0%} predicted probability."]

    driver_hints = {
        "tenure": "months of tenure is short",
        "monthly_charges": "monthly spend is high",
        "total_charges": "lifetime revenue is low",
        "contract_Month-to-month": "contract is month-to-month",
        "avg_monthly_charge": "average monthly spend is elevated",
        "tech_support": "no tech-support subscription",
        "online_security": "no online-security add-on",
    }

    for item in contributions[:3]:
        driver = item["feature"]
        hint = driver_hints.get(driver)
        if hint is None:
            continue
        direction = "increasing" if item["value"] > 0 else "reducing"
        lines.append(f"`{driver}` {hint}, {direction} churn likelihood by {abs(item['value']):.2f} (SHAP).")

    return {
        "risk_level": risk,
        "summary": lines[0],
        "factors": lines[1:],
    }


def persist_explanations(payload: dict[str, Any], filename: str = "global.json") -> None:
    """Save global SHAP artefacts into ``models/shap``."""
    DEFAULT_SHAP_DIR.mkdir(parents=True, exist_ok=True)
    path = DEFAULT_SHAP_DIR / filename
    import json

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_shap_artefacts() -> dict[str, Any]:
    """Load the persisted global SHAP summary for the Explainability page."""
    import json

    path = DEFAULT_SHAP_DIR / "global.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_local_explanation(customer_id: str) -> dict[str, Any] | None:
    """Load a previously cached local explanation, if present."""
    import json

    path = DEFAULT_MODEL_DIR / "explanations" / f"{customer_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)