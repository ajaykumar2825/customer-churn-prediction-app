"""Core ML serving: loads trained artefacts and executes predictions.

Kept database-agnostic so it can serve predictions with zero infrastructure.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from app.core.config import settings
from app.core.exceptions import ModelNotReady
from app.ml_feature_catalogue import FEATURE_ORDER

try:
    import shap

    _SHAP_AVAILABLE = True
except Exception:  # pragma: no cover
    shap = None  # type: ignore
    _SHAP_AVAILABLE = False


class ModelService:
    """Singleton holder for trained artefacts and the prediction API."""

    def __init__(self, model_dir: Path | None = None) -> None:
        self.model_dir = Path(model_dir or settings.model_dir)
        self._lock = threading.Lock()
        self._loaded: dict[str, Any] = {}

    # ------------------------------------------------------------------ loading
    def _require(self, name: str) -> Any:
        with self._lock:
            if name in self._loaded:
                return self._loaded[name]
        raise ModelNotReady()

    def load(self) -> None:
        """Load every artefact the API can serve."""
        directory = self.model_dir
        if not directory.exists():
            raise ModelNotReady()

        def read_json(filename: str) -> Any:
            path = directory / filename
            if not path.exists():
                return None
            with open(path, encoding="utf-8") as f:
                return json.load(f)

        pipeline: Pipeline | None = None
        pipeline_path = directory / "pipeline.joblib"
        if pipeline_path.exists():
            pipeline = joblib.load(pipeline_path)

        shims: dict[str, Any] = {
            "pipeline": pipeline,
            "preprocessor": joblib.load(directory / "preprocessor.joblib") if (directory / "preprocessor.joblib").exists() else None,
            "classifier": joblib.load(directory / "classifier.joblib") if (directory / "classifier.joblib").exists() else None,
            "meta": read_json("meta.json") or {},
            "threshold": read_json("threshold.json") or {"threshold": settings.default_threshold},
            "metrics": read_json("metrics.json") or {},
            "leaderboard": read_json("leaderboard.json") or [],
            "importance": read_json("importance.json") or {},
            "curves": read_json("curves.json") or {},
            "confusion": read_json("confusion.json") or {},
            "feature_names": read_json("feature_names.json") or [],
            "business": read_json("business_metrics.json") or {},
            "strategy": read_json("strategy.json") or {},
        }
        with self._lock:
            self._loaded = shims

    @property
    def ready(self) -> bool:
        return "pipeline" in self._loaded and self._loaded.get("pipeline") is not None

    def threshold_value(self) -> float:
        threshold = self._require("threshold")
        return float(threshold.get("threshold", settings.default_threshold))

    def model_name(self) -> str:
        meta = self._require("meta")
        return str(meta.get("model", "unknown"))

    # --------------------------------------------------------------- prediction
    def _dataframe(self, customer: dict[str, Any]) -> pd.DataFrame:
        columns = [f for f in FEATURE_ORDER if f in customer]
        return pd.DataFrame([customer])[columns]

    def predict(self, customer: dict[str, Any]) -> dict[str, Any]:
        pipeline = self._require("pipeline")
        threshold = self.threshold_value()
        df = self._dataframe(customer)
        probability = float(pipeline.predict_proba(df)[0, 1])
        result = self.build_prediction(customer, probability, threshold)
        return result

    def predict_batch(self, customers: list[dict[str, Any]]) -> dict[str, Any]:
        pipeline = self._require("pipeline")
        threshold = self.threshold_value()
        columns = [f for f in FEATURE_ORDER if f in customers[0]]
        df = pd.DataFrame(customers)[columns]
        t0 = time.perf_counter()
        probabilities = pipeline.predict_proba(df)[:, 1]
        latency_ms = (time.perf_counter() - t0) / max(len(customers), 1) * 1000
        results = [
            self.build_prediction(customer, float(prob), threshold, with_explanation=False)
            for customer, prob in zip(customers, probabilities, strict=False)
        ]
        return {
            "predictions": results,
            "summary": {
                "count": len(results),
                "mean_probability": round(float(np.mean(probabilities)), 4),
                "high_risk": int((probabilities >= settings.high_risk_threshold).sum()),
                "expected_churners": int((probabilities >= threshold).sum()),
                "latency_ms_per_row": round(latency_ms, 4),
            },
        }

    def build_prediction(
        self,
        customer: dict[str, Any],
        probability: float,
        threshold: float,
        with_explanation: bool = True,
    ) -> dict[str, Any]:
        risk = risk_level(probability)
        predicted_churn = bool(probability >= threshold)
        confidence_score = round(max(probability, 1 - probability), 4)

        contribution = None
        top_factors: list[dict[str, Any]] = []
        recommendation = retention_recommendation(risk, customer)

        if with_explanation:
            contribution = self.explain_input(customer, include_base=True)
            top_factors = contribution.get("top_factors", [])[:5]

        monthly = float(customer.get("monthly_charges", 0.0))
        return {
            "customer_id": str(customer.get("customer_id", "")),
            "probability": round(probability, 4),
            "risk_level": risk,
            "predicted_churn": predicted_churn,
            "confidence": confidence_score,
            "threshold": round(threshold, 4),
            "model": self.model_name(),
            "model_version": str(self._require("meta").get("run_id", "v1")),
            "revenue_at_risk_monthly": round(monthly * probability, 2),
            "retention_recommendation": recommendation,
            "top_factors": top_factors,
            "explanation": contribution,
        }

    # -------------------------------------------------------------- explain
    def explain_input(self, customer: dict[str, Any], include_base: bool = True) -> dict[str, Any] | None:
        """Local SHAP explanation for a single customer, with graceful fallback."""
        classifier = self._require("classifier")
        preprocessor = self._require("preprocessor")
        encoded_names = self._require("feature_names")
        df = self._dataframe(customer)
        transformed = preprocessor.transform(df)

        if _SHAP_AVAILABLE:
            try:
                explainer = _explainer(classifier, transformed)
                sv = explainer.shap_values(np.asarray(transformed.todense()) if hasattr(transformed, "todense") else transformed)
                if isinstance(sv, list):
                    sv = sv[1]
                base = _expected_value(explainer)
                values = np.asarray(sv).ravel()
                items = sorted(zip(encoded_names, values, strict=False), key=lambda kv: abs(float(kv[1])), reverse=True)
                contributions = [
                    {"feature": name, "value": round(float(v), 4)} for name, v in items
                ]
                return {
                    "base_value": round(float(base), 4),
                    "top_factors": contributions[:5],
                    "contributions": contributions,
                }
            except Exception:
                # fall through to global-importance fallback
                pass

        # Deterministic fallback: scale global importances by feature deviation.
        try:
            importance = self._require("importance").get("shap", {})
            global_importances = {item["feature"]: item["importance"] for item in importance.get("importances", [])}
            mean = np.abs(transformed.toarray() if hasattr(transformed, "toarray") else np.asarray(transformed)).ravel()
            contributions = [
                {"feature": name, "value": round(float(global_importances.get(name, 0.0)) * stroke, 4)}
                for name, stroke in zip(encoded_names, mean, strict=False)
            ]
            contributions.sort(key=lambda kv: abs(kv["value"]), reverse=True)
            return {"base_value": None, "top_factors": contributions[:5], "contributions": contributions}
        except Exception:
            return None

    def feature_importance(self) -> dict[str, Any]:
        importance = self._require("importance") or {}
        fallback = {
            "shap": {"importances": importance.get("shap", {}).get("importances", [])},
            "permutation": importance.get("permutation", []),
        }
        return fallback

    def metrics_payload(self) -> dict[str, Any]:
        return {
            "meta": self._require("meta"),
            "leaderboard": self._require("leaderboard"),
            "threshold": self._require("threshold"),
            "metrics": self._require("metrics"),
            "curves": self._require("curves"),
            "confusion": self._require("confusion"),
            "importance": self.feature_importance(),
        }


def risk_level(probability: float) -> str:
    """Bucket a probability into an executive risk label."""
    if probability >= settings.high_risk_threshold:
        return "high"
    if probability >= 0.5:
        return "medium"
    return "low"


def retention_recommendation(risk: str, customer: dict[str, Any]) -> str | None:
    """Rule-based retention guidance based on risk level."""
    contract = customer.get("contract", "")
    tech_support = customer.get("tech_support", False)
    if risk == "high":
        return "Immediate intervention: offer one-year contract with month-of-free service, waive early-exit fees, and unlock senior retention agent."
    if risk == "medium":
        if contract == "Month-to-month":
            return "Nudge to a one-year contract with a loyalty discount; add tech-support and online-security bundles."
        if not tech_support:
            return "Encourage tech-support subscription and proactive check-ins to reduce friction."
        return "Monitor closely; schedule a feedback call and consider a small loyalty credit."
    return None


def _expected_value(explainer) -> float:
    ev = explainer.expected_value
    if isinstance(ev, (list, tuple, np.ndarray)):
        values = np.asarray(ev, dtype="float64")
        return float(np.mean(values))
    return float(ev)


def _explainer(classifier, transformed):
    model_type = type(classifier).__name__
    if model_type in ("LogisticRegression", "LinearSVC", "RidgeClassifier", "SGDClassifier"):
        return shap.LinearExplainer(classifier, np.asarray(transformed.todense() if hasattr(transformed, "todense") else transformed))
    return shap.TreeExplainer(classifier)


model_service = ModelService()
