"""Optuna hyper-parameter tuning for the top four gradient-boosting models."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import optuna
from optuna.samplers import TPESampler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

from ml_pipeline.config import DEFAULT_MODEL_DIR, REPO_ROOT
from ml_pipeline.models import build_model

SEARCH_SPACES: dict[str, dict[str, tuple[str, Any, Any]]] = {
    "xgboost": {
        "max_depth": ("int", 3, 9),
        "learning_rate": ("float", 0.01, 0.25),
        "n_estimators": ("int", 150, 600),
        "subsample": ("float", 0.6, 1.0),
        "colsample_bytree": ("float", 0.5, 1.0),
        "min_child_weight": ("int", 1, 10),
        "scale_pos_weight": ("float", 0.5, 3.0),
    },
    "lightgbm": {
        "num_leaves": ("int", 15, 90),
        "learning_rate": ("float", 0.01, 0.2),
        "n_estimators": ("int", 150, 700),
        "min_child_samples": ("int", 10, 80),
        "subsample": ("float", 0.6, 1.0),
        "colsample_bytree": ("float", 0.5, 1.0),
        "reg_alpha": ("float", 1e-3, 10.0),
    },
    "catboost": {
        "depth": ("int", 4, 9),
        "learning_rate": ("float", 0.01, 0.2),
        "iterations": ("int", 200, 700),
        "l2_leaf_reg": ("float", 0.5, 10.0),
    },
    "random_forest": {
        "n_estimators": ("int", 200, 700),
        "max_depth": ("int", 6, 20),
        "min_samples_leaf": ("int", 1, 12),
        "max_features": ("categorical", ["sqrt", "log2", None]),
    },
}


class _Objective:
    """Objective function wrapping OOF AUC on a fixed CV split."""

    def __init__(self, model_name: str, X: np.ndarray, y: np.ndarray, cv: StratifiedKFold) -> None:
        self.model_name = model_name
        self.X, self.y = X, y
        self.cv = cv
        self.iteration = 0

    def __call__(self, trial: optuna.Trial) -> float:
        space = SEARCH_SPACES[self.model_name]
        params: dict[str, Any] = {}
        for name, spec in space.items():
            kind, *args = spec
            if kind == "int":
                params[name] = trial.suggest_int(name, *args)
            elif kind == "float":
                params[name] = trial.suggest_float(name, *args, log=True)
            else:
                params[name] = trial.suggest_categorical(name, args[0])
        model = build_model(self.model_name, **params)
        aucs = []
        for tr, va in self.cv.split(self.X, self.y):
            model.fit(self.X[tr], self.y[tr])
            aucs.append(roc_auc_score(self.y[va], model.predict_proba(self.X[va])[:, 1]))
        return float(np.mean(aucs))


def tune_model(
    model_name: str,
    X: np.ndarray,
    y: np.ndarray,
    n_trials: int = 40,
    timeout_seconds: int | None = None,
    seed: int = 42,
) -> dict[str, Any]:
    """Run an Optuna study for ``model_name`` on transformed data."""
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    sampler = TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler, study_name=f"churn-{model_name}")
    objective = _Objective(model_name, X, y, cv)
    study.optimize(
        objective,
        n_trials=n_trials,
        timeout=timeout_seconds,
        show_progress_bar=False,
    )
    best_params = study.best_params
    if model_name == "random_forest" and "max_features" in best_params and best_params["max_features"] is None:
        best_params["max_features"] = "sqrt"
    return {
        "model": model_name,
        "best_params": best_params,
        "best_value": float(study.best_value),
        "n_trials": len(study.trials),
        "study_name": study.study_name,
    }


def tune_models(X: np.ndarray, y: np.ndarray, names: list[str], n_trials: int = 40) -> dict[str, dict[str, Any]]:
    """Tune a list of models and persist a summary into the model directory."""
    results: dict[str, dict[str, Any]] = {}
    for name in names:
        results[name] = tune_model(name, X, y, n_trials=n_trials)
    assert DEFAULT_MODEL_DIR.exists(), REPO_ROOT
    return results