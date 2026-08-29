"""Evaluation utilities: metrics, cross-validation, thresholding, curves.

All curve data is exported as JSON-serialisable structures consumed directly
by the frontend charting pages.
"""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict

import ml_pipeline.config as cfg


def compute_metrics(y_true: np.ndarray, y_score: np.ndarray, threshold: float = 0.5) -> dict[str, Any]:
    """Derive the full metrics dictionary from labels and scores.

    Works with unlabelled data only when ``y_true`` is ``None``.
    """
    metrics: dict[str, Any] = {}
    if y_true is not None:
        y_pred = (y_score >= threshold).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
        metrics.update(
            {
                "accuracy": float(accuracy_score(y_true, y_pred)),
                "precision": float(precision_score(y_true, y_pred, zero_division=0)),
                "recall": float(recall_score(y_true, y_pred, zero_division=0)),
                "f1": float(f1_score(y_true, y_pred, zero_division=0)),
                "specificity": float(tn / (tn + fp)) if (tn + fp) else 0.0,
                "mcc": float(matthews_corrcoef(y_true, y_pred)),
                "roc_auc": float(roc_auc_score(y_true, y_score)),
                "pr_auc": float(average_precision_score(y_true, y_score)),
                "brier": float(brier_score_loss(y_true, y_score)),
                "log_loss": float(log_loss(y_true, y_score)),
            }
        )
    return metrics


def optimize_threshold(y_true: np.ndarray, y_score: np.ndarray) -> dict[str, Any]:
    """Pick the decision threshold that maximises F1.

    Returns the threshold and the style-free business loss (churners missed
    have an assumed cost, so this also guards the low end of the curve).
    """
    thresholds = np.linspace(0.05, 0.95, 181)
    best_t, best_f1 = 0.5, -1.0
    best_detail: dict[str, Any] = {}
    for t in thresholds:
        y_pred = (y_score >= t).astype(int)
        f = f1_score(y_true, y_pred, zero_division=0)
        if f > best_f1:
            best_f1, best_t = float(f), float(t)
    best_detail = compute_metrics(y_true, y_score, best_t)
    return {"threshold": round(best_t, 3), **best_detail}


def cross_validated_scores(clf: Any, X: np.ndarray, y: np.ndarray, n_splits: int = 5) -> dict[str, Any]:
    """Out-of-fold metrics via StratifiedKFold + ``cross_val_predict``."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    y_score = cross_val_predict(clf, X, y, cv=skf, method="predict_proba")[:, 1]
    metrics = compute_metrics(y, y_score)
    metrics["n_folds"] = n_splits
    metrics["ooc_scores"] = y_score.tolist()
    metrics["ooc_labels"] = y.tolist()
    return metrics


def build_curves(y_true: np.ndarray, y_score: np.ndarray, n_quantiles: int = 40) -> dict[str, Any]:
    """All curve payloads for the Model Performance page."""
    fpr, tpr, _ = roc_curve(y_true, y_score)
    precision, recall, _ = precision_recall_curve(y_true, y_score)

    # Lift & gain
    order = np.argsort(-y_score)
    sorted_y = y_true[order]
    total_positive = sorted_y.sum()
    cumulative = np.cumsum(sorted_y)
    population = np.arange(1, len(sorted_y) + 1)
    gain = cumulative / total_positive
    lift = gain / (population / len(sorted_y))

    # Calibration (pandas/numpy 2.x safe)
    prob_true, prob_pred = calibration_curve(y_true, y_score, n_bins=10)

    return {
        "roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "pr": {"precision": precision.tolist(), "recall": recall.tolist()},
        "lift": {
            "population_percent": np.linspace(0, 100, len(lift)).tolist(),
            "lift": lift.tolist(),
        },
        "gain": {
            "population_percent": np.linspace(0, 100, len(gain)).tolist(),
            "gain": gain.tolist(),
        },
        "calibration": {
            "prob_pred": prob_pred.tolist(),
            "prob_true": prob_true.tolist(),
        },
    }


def learning_curve_data(history: dict[str, list[float]]) -> dict[str, Any]:
    """Learning curve from recorded train/validation scores during tuning."""
    return {
        "train_scores": history.get("train", []),
        "validation_scores": history.get("validation", []),
    }


def confusion_matrix_payload(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    """Confusion matrix as a labelled payload."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {"matrix": [[int(tn), int(fp)], [int(fn), int(tp)]], "labels": ["Non-churn", "Churn"]}


def _default_nan(value: Any, fallback: float = 0.0) -> float:
    """Convert numpy NaN to a JSON-safe fallback."""
    return fallback if value is None or (isinstance(value, float) and math.isnan(value)) else value


from pathlib import Path
import json

def save_json(payload: dict[str, Any], path) -> None:
    """Persist a JSON payload at `path`."""
    path = Path(path)

    # Create reports directory automatically
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=_default_nan)