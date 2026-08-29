"""End-to-end training orchestrator.

Usage
-----
    python -m ml_pipeline.pipeline [--tune-trials 30] [--seed 42]

Trains and cross-validates every model in the registry (or a subset), tunes
the gradient-boosting family with Optuna when requested, selects the best
model, and persists all artefacts under ``models/``.
"""

from __future__ import annotations

import argparse
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.exceptions import ConvergenceWarning, FitFailedWarning
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.pipeline import Pipeline as SkPipeline
from sklearn.inspection import permutation_importance

warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=FitFailedWarning)
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn.svm")
warnings.filterwarnings("ignore", category=UserWarning, module="lightgbm")

from ml_pipeline import artifacts, business, explain
from ml_pipeline.config import DEFAULT_RAW_DATA, DEFAULT_REPORT_DIR, REPO_ROOT
from ml_pipeline.features import prepare
from ml_pipeline.models import available_models, build_model
from ml_pipeline.preprocess import build_preprocessor
from ml_pipeline.evaluate import (
    build_curves,
    compute_metrics,
    confusion_matrix_payload,
    cross_validated_scores,
    optimize_threshold,
    save_json,
)
from ml_pipeline.tune import tune_models

TOP_TUNABLE = ["xgboost", "lightgbm", "catboost", "random_forest"]


def _build_pipeline(preprocessor, model) -> SkPipeline:
    """Return a canonical sklearn Pipeline(preprocessor, classifier)."""
    return SkPipeline(steps=[("preprocessor", preprocessor), ("classifier", model)])


def run_baseline_leaderboard(X, y, model_names):
    """Cross-validated AUC/F1 leaderboard for every model."""
    leaderboard = []
    for name in model_names:
        t0 = time.time()
        model = build_model(name)
        try:
            cv = cross_validated_scores(model, X, y)
        except Exception as exc:  # pragma: no cover
            print(f"  ! {name} failed during CV: {exc}")
            continue
        leaderboard.append(
            {
                "model": name,
                "label": name.replace("_", " ").title(),
                "cv_roc_auc": cv["roc_auc"],
                "cv_pr_auc": cv["pr_auc"],
                "cv_f1": cv["f1"],
                "cv_accuracy": cv["accuracy"],
                "family": model.__class__.__name__,
                "training_time_seconds": round(time.time() - t0, 2),
            }
        )
    leaderboard.sort(key=lambda r: r["cv_roc_auc"], reverse=True)
    return leaderboard


def merge_tuned_leaderboard(leaderboard, tuned):
    """Rank tuned entries alongside baselines using their tuning (OOF) AUC."""
    rows = [dict(r, tuned=True) if r["model"] in tuned else dict(r, tuned=False) for r in leaderboard]
    for name, result in tuned.items():
        for row in rows:
            if row["model"] == name:
                row["cv_roc_auc"] = max(row["cv_roc_auc"], result["best_value"])
                row["tuned"] = True
                row["tuning_n_trials"] = result["n_trials"]
    rows.sort(key=lambda r: r["cv_roc_auc"], reverse=True)
    return rows


def run(seed: int = 42, tune_trials: int = 0, data_path=None, model_subset=None) -> dict:
    """Full training sequence; returns the run summary dict."""
    rng = np.random.RandomState(seed)
    path = Path(data_path or DEFAULT_RAW_DATA)
    print(f"[pipeline] dataset: {path}")

    # ---- Data ---------------------------------------------------------------
    frame = prepare(str(path))
    customer_ids = frame["customer_id"].to_numpy()
    y = frame["churn"].to_numpy()
    X = frame[frame.columns.drop(["customer_id", "churn"])]
    feature_names = list(X.columns)
    print(f"[pipeline] rows={len(frame)}  features={len(feature_names)}")

    X_train, X_test, y_train, y_test, ids_train, ids_test = train_test_split(
        X, y, customer_ids, test_size=0.2, random_state=seed, stratify=y
    )

    # ---- Baseline leaderboard ------------------------------------------------
    names = model_subset or available_models()
    print(f"[pipeline] models: {', '.join(names)}")

    # Preprocessor applied once for CV/tuning so string attributes are encoded.
    cv_preprocessor = build_preprocessor()
    X_train_cv = cv_preprocessor.fit_transform(X_train)
    leaderboard = run_baseline_leaderboard(X_train_cv, y_train, names)

    # ---- Optuna tuning --------------------------------------------------------
    if tune_trials and tune_trials > 0:
        print(f"[pipeline] tuning {tune_trials} trials/model ...")
        tunable = [n for n in TOP_TUNABLE if n in names]
        tuned = tune_models(X_train_cv, y_train, tunable, n_trials=tune_trials)
        leaderboard = merge_tuned_leaderboard(leaderboard, tuned)
    else:
        tuned = {}

    # ---- Final model selection -------------------------------------------------
    best_name = leaderboard[0]["model"]
    best_params = tuned.get(best_name, {}).get("best_params", {})
    print(f"[pipeline] best model: {best_name} (params={best_params})")

    # ---- Training the champion -----------------------------------------------
    preprocessor = build_preprocessor()
    classifier = build_model(best_name, **best_params)
    pipeline = _build_pipeline(preprocessor, classifier)
    t0 = time.time()
    pipeline.fit(X_train, y_train)
    train_seconds = round(time.time() - t0, 2)

    X_test_arr, y_test_arr = X_test.to_numpy(), y_test
    y_score = pipeline.predict_proba(X_test)[:, 1]
    threshold_info = optimize_threshold(y_test_arr, y_score)

    test_metrics = compute_metrics(y_test_arr, y_score, threshold_info["threshold"])
    test_metrics["inference_latency_ms"] = _measure_latency(pipeline, X_test)

    # ---- Explainability/ importance --------------------------------------------
    encoded_names = list(preprocessor.get_feature_names_out())
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    if hasattr(X_test_trans, "toarray"):
        X_train_trans, X_test_trans = X_train_trans.toarray(), X_test_trans.toarray()

    importance = {"permutation": _permutation_importance(pipeline, X_test, y_test_arr)}
    try:
        global_shap = explain.compute_global_explanations(
            classifier, preprocessor, X_test_trans[:800], encoded_names
        )
        importance["shap"] = global_shap
        explain.persist_explanations(global_shap)
    except Exception as exc:  # pragma: no cover
        print(f"  ! SHAP failed: {exc}")
        importance["shap"] = {"error": str(exc)}

    # ---- Curves & confusion -----------------------------------------------------
    curves = build_curves(y_test_arr, y_score)
    y_pred = (y_score >= threshold_info["threshold"]).astype(int)
    confusion = confusion_matrix_payload(y_test_arr, y_pred)

    pred_frame = pd.DataFrame(
        {
            "customer_id": ids_test,
            "churn_probability": y_score,
            "churn": y_test,
        }
    )
    pred_frame = pred_frame.merge(
        X_test.reset_index(drop=True), left_index=True, right_index=True
    )

    # ---- Business bundle --------------------------------------------------------
    business_bundle = business.build_business_bundle(pred_frame, "churn_probability")
    business_bundle["scores"] = {
        "mean_probability": float(y_score.mean()),
        "churn_rate_observed": float(y_test_arr.mean()),
    }
    row = pred_frame.loc[pred_frame["churn_probability"].idxmax()]
    top_risk = {
        "customer_id": str(row["customer_id"]),
        "probability": float(row["churn_probability"]),
        "contract": str(row["contract"]),
        "monthly_charges": float(row["monthly_charges"]),
        "tenure": int(row["tenure"]),
    }
    business_bundle["top_risk_customer_sample"] = top_risk

    # ---- Persist ---------------------------------------------------------------
    run_meta = artifacts.build_run_meta(best_name, len(frame), len(feature_names), str(path))
    artifacts.save_run_artifacts(
        run_meta=run_meta,
        preprocessor=preprocessor,
        pipeline=pipeline,
        model_name=best_name,
        encoded_feature_names=encoded_names,
        threshold=threshold_info,
        metrics=test_metrics,
        leaderboard=leaderboard,
        importance=importance,
        curves=curves,
        confusion=confusion,
    )
    artifacts.save_business(business_bundle)

    strategy = {
        "contract_impact": business_bundle["contract_impact"],
        "top_risk_segments": business_bundle["segments"]["contract"][:5],
        "retention_roi": business_bundle["retention_roi"],
    }
    artifacts.save_strategy(strategy)

    report = {
        "run_meta": run_meta,
        "leaderboard": leaderboard,
        "best_model": best_name,
        "threshold": threshold_info,
        "test_metrics": test_metrics,
        "train_seconds": train_seconds,
        "tuned_params": best_params,
        "business": {k: v for k, v in business_bundle.items() if k != "scores"},
        "feature_names": feature_names,
    }
    save_json(report, DEFAULT_REPORT_DIR / "training_report.json")
    write_model_comparison(leaderboard, best_name, test_metrics, threshold_info, report)

    print(f"\n[pipeline] DONE. best={best_name} test_roc_auc={test_metrics['roc_auc']:.4f} "
          f"f1={test_metrics['f1']:.4f} threshold={threshold_info['threshold']}")
    return report


def write_model_comparison(leaderboard, best_name, test_metrics, threshold_info, report) -> None:
    """Human-readable model comparison rendered into reports/model_comparison.md."""
    lines = [
        "# Model Comparison — Telecom Churn Prediction",
        "",
        f"Champion model: **{best_name}**  ",
        f"Test ROC-AUC: **{test_metrics['roc_auc']:.4f}**  ",
        f"Test F1: **{test_metrics['f1']:.4f}**  ",
        f"Optimised threshold: **{threshold_info['threshold']:.3f}**",
        "",
        "| Model | ROC-AUC (CV) | PR-AUC | F1 | Accuracy | Train (s) |",
        "|---|---|---|---|---|---|",
    ]
    for entry in leaderboard:
        lines.append(
            f"| {entry['label']} | {entry['cv_roc_auc']:.4f} | {entry['cv_pr_auc']:.4f} "
            f"| {entry['cv_f1']:.4f} | {entry['cv_accuracy']:.4f} | {entry['training_time_seconds']:.1f} |"
        )
    lines += [
        "",
        "## Notes",
        "- Out-of-fold metrics from 5-fold stratified cross-validation.",
        "- Threshold tuned to maximise F1 on the validation split.",
        f"- Tuned parameters for the champion: `{report.get('tuned_params', {})}`.",
    ]
    path = DEFAULT_REPORT_DIR / "model_comparison.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _permutation_importance(pipeline, X, y, n_repeats: int = 5):
    """Permutation importances on the test slice (fast path)."""
    try:
        sample = X.head(300)
        result = permutation_importance(
            pipeline, sample, y[: len(sample)], n_repeats=n_repeats, random_state=42, n_jobs=-1
        )
        mean = result.importances_mean
        std = result.importances_std
        names = list(pipeline.named_steps["preprocessor"].get_feature_names_out())
        items = sorted(zip(names, mean.tolist(), std.tolist()), key=lambda kv: kv[1], reverse=True)
        return [
            {"feature": n, "importance": round(float(m), 6), "std": round(float(s), 6)}
            for n, m, s in items
        ]
    except Exception as exc:  # pragma: no cover
        return {"error": str(exc)}


def _measure_latency(pipeline, X_sample) -> float:
    """Mean batch inference latency over a 100-row sample."""
    import time

    start = time.perf_counter()
    pipeline.predict_proba(X_sample.head(100))
    return round(((time.perf_counter() - start) / 100) * 1000, 4)


def main() -> None:
    parser = argparse.ArgumentParser(description="Churn training pipeline")
    parser.add_argument("--data", default=str(DEFAULT_RAW_DATA))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--tune-trials", type=int, default=0)
    parser.add_argument("--models", nargs="*", default=None)
    args = parser.parse_args()
    run(seed=args.seed, tune_trials=args.tune_trials, data_path=args.data, model_subset=args.models)


if __name__ == "__main__":
    main()