"""Model registry: every classifier the platform can train.

Each entry exposes a ``factory`` taking keyword arguments and a
``default_params`` dict; :func:`build_model` merges overrides on top of the
defaults so Optuna-tuned parameters never collide with hard-coded kwargs.
"""

from __future__ import annotations

from typing import Any

from sklearn.ensemble import (
    GradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

try:
    from xgboost import XGBClassifier
except Exception:  # pragma: no cover - optional dependency
    XGBClassifier = None  # type: ignore

try:
    from lightgbm import LGBMClassifier
except Exception:  # pragma: no cover - optional dependency
    LGBMClassifier = None  # type: ignore


def _catboost_factory(**kwargs: Any):
    from catboost import CatBoostClassifier

    def _coerce_kwargs(items: dict[str, Any]) -> dict[str, Any]:
        """Rename optuna-produced aliases into catboost spelling."""
        if "iterations" in items and "n_estimators" in items:
            items.pop("iterations")
        return items

    params = _coerce_kwargs(dict(kwargs))
    return CatBoostClassifier(verbose=0, allow_writing_files=False, **params)


MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "logistic_regression": {
        "label": "Logistic Regression",
        "family": "linear",
        "description": "Linear baseline with strong explainability.",
        "factory": LogisticRegression,
        "default_params": {"max_iter": 2000, "class_weight": "balanced", "random_state": 42},
    },
    "decision_tree": {
        "label": "Decision Tree",
        "family": "tree",
        "description": "Interpretable single tree baseline.",
        "factory": DecisionTreeClassifier,
        "default_params": {
            "max_depth": 8,
            "min_samples_leaf": 10,
            "class_weight": "balanced",
            "random_state": 42,
        },
    },
    "random_forest": {
        "label": "Random Forest",
        "family": "ensemble",
        "description": "Bagged forest; robust and performant.",
        "factory": RandomForestClassifier,
        "default_params": {
            "n_estimators": 400,
            "max_depth": None,
            "min_samples_leaf": 2,
            "class_weight": "balanced_subsample",
            "n_jobs": -1,
            "random_state": 42,
        },
    },
    "gradient_boosting": {
        "label": "Gradient Boosting",
        "family": "ensemble",
        "description": "Scikit-learn GBM baseline.",
        "factory": GradientBoostingClassifier,
        "default_params": {
            "n_estimators": 300,
            "learning_rate": 0.05,
            "max_depth": 4,
            "min_samples_leaf": 15,
            "random_state": 42,
        },
    },
    "svm": {
        "label": "Support Vector Machine",
        "family": "kernel",
        "description": "RBF SVM; slow but strong on small data.",
        "factory": SVC,
        "default_params": {
            "kernel": "rbf",
            "C": 1.0,
            "gamma": "scale",
            "class_weight": "balanced",
            "probability": True,
            "random_state": 42,
        },
    },
    "xgboost": {
        "label": "XGBoost",
        "family": "gradient_boosting",
        "description": "Optimised gradient boosting with native tree SHAP.",
        "factory": XGBClassifier,
        "default_params": {
            "n_estimators": 400,
            "learning_rate": 0.05,
            "max_depth": 5,
            "subsample": 0.9,
            "colsample_bytree": 0.8,
            "min_child_weight": 1,
            "scale_pos_weight": 1.0,
            "eval_metric": "aucpr",
            "random_state": 42,
            "n_jobs": -1,
        },
    },
    "lightgbm": {
        "label": "LightGBM",
        "family": "gradient_boosting",
        "description": "Fast gradient boosting with histogram trees.",
        "factory": LGBMClassifier,
        "default_params": {
            "n_estimators": 500,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_child_samples": 20,
            "subsample": 0.9,
            "colsample_bytree": 0.8,
            "class_weight": "balanced",
            "random_state": 42,
            "n_jobs": -1,
            "verbose": -1,
        },
    },
    "catboost": {
        "label": "CatBoost",
        "family": "gradient_boosting",
        "description": "Ordered boosting, handles categoricals natively.",
        "factory": _catboost_factory,
        "default_params": {
            "iterations": 500,
            "learning_rate": 0.05,
            "depth": 6,
            "random_seed": 42,
            "auto_class_weights": "Balanced",
        },
    },
}


def available_models() -> list[str]:
    """Names of models whose libraries can be imported in this environment."""
    names = list(MODEL_REGISTRY)
    if XGBClassifier is None:
        names.remove("xgboost")
    if LGBMClassifier is None:
        names.remove("lightgbm")
    if "catboost" in names:
        try:
            import catboost  # noqa: F401

            # guard against catboost being non-functional on the current py
            from catboost import CatBoostClassifier  # noqa: F401
        except Exception:
            names.remove("catboost")
    return names


def build_model(name: str, **overrides: Any):
    """Instantiate a model, optionally overriding some hyper-parameters."""
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model '{name}'")
    entry = MODEL_REGISTRY[name]
    params = {**entry["default_params"], **overrides}
    model = entry["factory"](**params)
    return model