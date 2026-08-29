"""Cached loaders for the dataset, trained artifacts and feature metadata.

Artifacts are loaded using the new-style names first (``best_model.pkl``,
``preprocessor.pkl``, ``label_encoder.pkl``, ``feature_metadata.json``) and
fall back to the canonical joblib/json artefacts produced by the pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from ml_pipeline.config import DEFAULT_MODEL_DIR, DEFAULT_SHAP_DIR, DEFAULT_RAW_DATA
from ml_pipeline.features import prepare
from ml_pipeline.feature_catalogue import ML_FEATURE_CATALOGUE, FEATURE_ORDER

_MODEL_ALIASES = {
    "pipeline": ("pipeline.joblib", "best_model.pkl"),
    "classifier": ("classifier.joblib", "best_model.pkl"),
    "preprocessor": ("preprocessor.joblib", "preprocessor.pkl"),
}

_JSON_ARTIFACTS = {
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
    "shap_global": str(DEFAULT_SHAP_DIR / "global.json"),
}


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


@st.cache_data(show_spinner=False)
def load_data() -> "pd.DataFrame":
    """The engineered modelling frame (7032 rows x 21 cols)."""
    return prepare(str(DEFAULT_RAW_DATA))


@st.cache_data(show_spinner=False)
def load_feature_metadata() -> dict[str, dict]:
    """Feature metadata dict, persisted as ``models/feature_metadata.json``."""
    meta = {
        "feature_order": FEATURE_ORDER,
        "n_features": len(FEATURE_ORDER),
        "catalogue": ML_FEATURE_CATALOGUE,
    }
    path = DEFAULT_MODEL_DIR / "feature_metadata.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2)
    except Exception:
        pass
    return ML_FEATURE_CATALOGUE


# ------------------------------------------------------------------------
# Model artifacts
# ------------------------------------------------------------------------
_SESSION_RESULT_KEY = "_artifacts_result"


def _load_first(candidates: list[str]):
    from joblib import load as jload

    for name in candidates:
        path = DEFAULT_MODEL_DIR / name
        if path.exists():
            return jload(path)
    return None


def load_model_bundle() -> dict[str, Any] | None:
    """All trained artifacts, named consistently for every page.

    Returns ``None`` only when the pipeline is missing entirely.
    """
    if _SESSION_RESULT_KEY in st.session_state:
        return st.session_state[_SESSION_RESULT_KEY]

    pipeline = _load_first(_MODEL_ALIASES["pipeline"])
    if pipeline is None:
        pipeline = _auto_train()
    if pipeline is None:
        return None

    classifier = _load_first(_MODEL_ALIASES["classifier"]) or pipeline
    preprocessor = _load_first(_MODEL_ALIASES["preprocessor"]) or pipeline.named_steps.get(
        "preprocessor", None
    )

    json_artifacts: dict[str, Any] = {}
    for key, filename in _JSON_ARTIFACTS.items():
        json_artifacts[key] = _read_json(DEFAULT_MODEL_DIR / filename)

    bundle = {
        "pipeline": pipeline,
        "classifier": pipeline.named_steps.get("classifier", classifier),
        "preprocessor": preprocessor,
        **json_artifacts,
    }
    bundle["feature_names"] = bundle["feature_names"] or []
    bundle["threshold"] = bundle["threshold"] or {"threshold": 0.5}
    bundle["shap_global"] = bundle["shap_global"] or {}

    st.session_state[_SESSION_RESULT_KEY] = bundle
    return bundle


def _auto_train():
    """Fallback: train the champion model using the pipeline (heavy)."""
    st.warning(
        "No trained artifacts were found under `models/`. Training the pipeline now — "
        "this can take several minutes."
    )
    try:
        import ml_pipeline.pipeline as pipeline  # noqa: N813

        pipeline.run()
        return _load_first(_MODEL_ALIASES["pipeline"])
    except Exception as exc:  # pragma: no cover
        st.error(f"Automatic training failed: {exc}")
        return None