"""Artifact persistence: versioned save/load for models, preprocessors and metadata."""

from __future__ import annotations

import json
import os
import time
import uuid
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib

from ml_pipeline.config import DEFAULT_MODEL_DIR, DEFAULT_SHAP_DIR

ARTIFACT_FILES = {
    "preprocessor": "preprocessor.joblib",
    "classifier": "classifier.joblib",
    "pipeline": "pipeline.joblib",
    "meta": "meta.json",
    "feature_names": "feature_names.json",
    "threshold": "threshold.json",
    "metrics": "metrics.json",
    "leaderboard": "leaderboard.json",
    "importance": "importance.json",
    "curves": "curves.json",
    "confusion": "confusion.json",
    "business": "business_metrics.json",
    "strategy": "strategy.json",
}


def _write_json(payload: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_joblib(obj: Any, filename: str, directory: Path | None = None) -> Path:
    """Joblib-dump ``obj`` into the artifact directory."""
    directory = directory or DEFAULT_MODEL_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    joblib.dump(obj, path)
    return path


def load_joblib(filename: str, directory: Path | None = None) -> Any:
    directory = directory or DEFAULT_MODEL_DIR
    return joblib.load(directory / filename)


def save_run_artifacts(
    *,
    run_meta: dict[str, Any],
    preprocessor: Any,
    pipeline: Any,
    model_name: str,
    encoded_feature_names: list[str],
    threshold: dict[str, Any],
    metrics: dict[str, Any],
    leaderboard: list[dict[str, Any]],
    importance: dict[str, Any],
    curves: dict[str, Any],
    confusion: dict[str, Any],
) -> None:
    """Persist everything produced by a successful training run."""
    ensure_dirs()
    save_joblib(preprocessor, ARTIFACT_FILES["preprocessor"])
    save_joblib(pipeline, ARTIFACT_FILES["pipeline"])
    save_joblib(pipeline.named_steps.get("classifier", pipeline), ARTIFACT_FILES["classifier"])

    _write_json(run_meta, DEFAULT_MODEL_DIR / ARTIFACT_FILES["meta"])
    _write_json(encoded_feature_names, DEFAULT_MODEL_DIR / ARTIFACT_FILES["feature_names"])
    _write_json(threshold, DEFAULT_MODEL_DIR / ARTIFACT_FILES["threshold"])
    _write_json(metrics, DEFAULT_MODEL_DIR / ARTIFACT_FILES["metrics"])
    _write_json(leaderboard, DEFAULT_MODEL_DIR / ARTIFACT_FILES["leaderboard"])
    _write_json(importance, DEFAULT_MODEL_DIR / ARTIFACT_FILES["importance"])
    _write_json(curves, DEFAULT_MODEL_DIR / ARTIFACT_FILES["curves"])
    _write_json(confusion, DEFAULT_MODEL_DIR / ARTIFACT_FILES["confusion"])


def build_run_meta(model_name: str, n_rows: int, n_features: int, data: str) -> dict[str, Any]:
    """Standard run metadata used by the Model Performance page."""
    return {
        "model": model_name,
        "model_label": model_name.replace("_", " ").title(),
        "trained_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "run_id": uuid.uuid4().hex[:12],
        "n_rows": n_rows,
        "n_features": n_features,
        "dataset": os.path.basename(data),
        "python": sys.version.split()[0],
        "packages": {
            "sklearn": _version("sklearn"),
            "pandas": _version("pandas"),
            "numpy": _version("numpy"),
        },
    }


def _version(module: str) -> str:
    try:
        return __import__(module).__version__
    except Exception:
        return "unknown"


def ensure_dirs(force: bool = False) -> None:
    DEFAULT_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_SHAP_DIR.mkdir(parents=True, exist_ok=True)


def save_business(payload: dict[str, Any]) -> None:
    _write_json(payload, DEFAULT_MODEL_DIR / ARTIFACT_FILES["business"])


def save_strategy(payload: dict[str, Any]) -> None:
    _write_json(payload, DEFAULT_MODEL_DIR / ARTIFACT_FILES["strategy"])


def load_latest_artifacts() -> dict[str, Any]:
    """Load every persisted artifact expected by the backend."""
    return {
        name: (load_joblib(f) if not name.endswith("json") else _read_json(DEFAULT_MODEL_DIR / f))
        for name, f in ARTIFACT_FILES.items()
    }


def load_artifacts_json(name: str) -> Any:
    """Load a JSON artifact by its catalog key or literal filename."""
    if name in ARTIFACT_FILES:
        return _read_json(DEFAULT_MODEL_DIR / ARTIFACT_FILES[name])
    return _read_json(DEFAULT_MODEL_DIR / name)