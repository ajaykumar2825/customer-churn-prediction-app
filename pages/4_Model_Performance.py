"""Page 4 — Model Registry / Performance (champion deep-dive)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from components import charts
from components.layout import hero, section_title, stat_tiles
from components.metric_cards import metric_row
from components.sidebar import model_status_sidebar
from utils import loader, stats
from utils.formatting import fmt_percent

bundle = loader.load_model_bundle()
if bundle is None:
    st.stop()

model_status_sidebar(bundle)
meta = bundle["meta"] or {}
metrics = bundle["metrics"] or {}
threshold = float((bundle["threshold"] or {}).get("threshold", 0.5))
model_label = (meta.get("model_label") or meta.get("model") or "xgboost").title()

hero(
    "Model Performance",
    f"Every metric on the held-out test split, the full threshold story, calibration, chaos "
    "matrix and the champion's global feature effects.",
    meta=f'<span class="cap-badge">{meta.get("model", "model")} · {str(meta.get("run_id", "—"))[:8]}</span>',
)


# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Reproducing held-out split…")
def _held_out() -> tuple[np.ndarray, np.ndarray]:
    from sklearn.model_selection import train_test_split

    from ml_pipeline.config import DEFAULT_RAW_DATA
    from ml_pipeline.features import prepare

    frame = prepare(str(DEFAULT_RAW_DATA))
    y = frame["churn"].to_numpy()
    X = frame[frame.columns.drop(["customer_id", "churn"])]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    proba = bundle["pipeline"].predict_proba(X_test)[:, 1]
    return y_test, proba


@st.cache_resource(show_spinner="Sweeping decision thresholds…")
def _threshold_sweep() -> dict:
    from sklearn.metrics import accuracy_score, f1_score, recall_score

    y_true, y_score = _held_out()
    thresholds = np.linspace(0.05, 0.95, 91)
    f1s, accs, recs = [], [], []
    for t in thresholds:
        pred = (y_score >= t).astype(int)
        f1s.append(f1_score(y_true, pred, zero_division=0))
        accs.append(accuracy_score(y_true, pred))
        recs.append(recall_score(y_true, pred, zero_division=0))
    best_i = int(np.argmax(f1s))
    return {
        "thresholds": thresholds.tolist(),
        "f1": f1s,
        "accuracy": accs,
        "recall": recs,
        "best_threshold": float(thresholds[best_i]),
        "best_f1": float(f1s[best_i]),
    }


@st.cache_resource(show_spinner="Building the learning curve…")
def _learning_curve() -> dict:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split

    from ml_pipeline.config import DEFAULT_RAW_DATA
    from ml_pipeline.features import prepare

    frame = prepare(str(DEFAULT_RAW_DATA))
    y = frame["churn"].to_numpy()
    X = frame[frame.columns.drop(["customer_id", "churn"])]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    X_tr = bundle["preprocessor"].transform(X_tr)
    if hasattr(X_tr, "toarray"):
        X_tr = X_tr.toarray()
    X_te = bundle["preprocessor"].transform(X_te)
    if hasattr(X_te, "toarray"):
        X_te = X_te.toarray()

    fractions = [0.05, 0.1, 0.2, 0.4, 0.8]
    train_scores, val_scores = [], []
    for frac in fractions:
        n = max(50, int(len(X_tr) * frac))
        mdl = RandomForestClassifier(n_estimators=150, random_state=42, n_jobs=-1)
        mdl.fit(X_tr[:n], y_tr[:n])
        train_scores.append(roc_auc_score(y_tr[:n], mdl.predict_proba(X_tr[:n])[:, 1]))
        val_scores.append(roc_auc_score(y_te, mdl.predict_proba(X_te)[:, 1]))
    return {
        "labels": [f"{int(f * 100)}%" for f in fractions],
        "train": train_scores,
        "validation": val_scores,
    }


# ---- Primary KPI row ------------------------------------------------------------
metric_row(
    [
        {"label": "ROC-AUC", "value": f"{metrics.get('roc_auc', 0):.4f}", "accent": "primary", "hint": "discrimination"},
        {"label": "F1 score", "value": f"{metrics.get('f1', 0):.4f}", "accent": "cyan", "hint": f"@ thresh {fmt_percent(threshold, 1)}"},
        {"label": "Precision", "value": fmt_percent(metrics.get("precision", 0), 1), "accent": "success", "hint": "of flagged churners"},
        {"label": "Recall", "value": fmt_percent(metrics.get("recall", 0), 1), "accent": "warning", "hint": "of true churners caught"},
        {"label": "Accuracy", "value": fmt_percent(metrics.get("accuracy", 0), 1), "accent": "danger", "hint": f"@ thresh {fmt_percent(threshold, 1)}"},
    ]
)

# ---- Secondary metrics ------------------------------------------------------------
metric_row(
    [
        {"label": "PR-AUC", "value": f"{metrics.get('pr_auc', 0):.4f}", "accent": "cyan", "hint": "average precision"},
        {"label": "MCC", "value": f"{metrics.get('mcc', 0):.4f}", "accent": "primary", "hint": "balanced accuracy"},
        {"label": "Specificity", "value": fmt_percent(metrics.get("specificity", 0), 1), "accent": "success", "hint": "true negative rate"},
        {"label": "Brier score", "value": f"{metrics.get('brier', 0):.4f}", "accent": "warning", "hint": "calibration error"},
        {"label": "Log-loss", "value": f"{metrics.get('log_loss', 0):.4f}", "accent": "danger", "hint": "cross-entropy"},
    ]
)

# ---- Curves -----------------------------------------------------------------------
section_title("Discrimination & thresholds")
c1, c2 = st.columns(2, gap="large")
curves = bundle["curves"] or {}
with c1:
    st.markdown("**ROC curve**")
    st.plotly_chart(charts.roc_curve(curves["roc"]["fpr"], curves["roc"]["tpr"], metrics.get("roc_auc", 0)),
                    width="stretch", config={"displayModeBar": False})
with c2:
    st.markdown("**Precision–recall curve**")
    st.plotly_chart(charts.pr_curve(curves["pr"]["precision"], curves["pr"]["recall"], metrics.get("pr_auc", 0)),
                    width="stretch", config={"displayModeBar": False})

c1, c2 = st.columns(2, gap="large")
sweep = _threshold_sweep()
with c1:
    st.markdown("**Threshold optimization — F1(max)**")
    st.plotly_chart(
        charts.threshold_curve(
            np.array(sweep["thresholds"]), np.array(sweep["f1"]),
            np.array(sweep["accuracy"]), np.array(sweep["recall"]), sweep["best_threshold"],
        ),
        width="stretch",
        config={"displayModeBar": False},
    )
with c2:
    st.markdown("**Calibration**")
    if "calibration" in curves:
        st.plotly_chart(
            charts.calibration(curves["calibration"]["prob_pred"], curves["calibration"]["prob_true"]),
            width="stretch", config={"displayModeBar": False},
        )
    else:  # pragma: no cover
        st.info("Calibration curve not present in artifacts.")

lift, gain = charts.lift_gain_curves(curves)
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Lift curve**")
    st.plotly_chart(lift, width="stretch", config={"displayModeBar": False})
with c2:
    st.markdown("**Cumulative gain**")
    st.plotly_chart(gain, width="stretch", config={"displayModeBar": False})

# ---- Confusion + leaderboard ---------------------------------------------------------
section_title("Confusion matrix & model leaderboard")
c1, c2 = st.columns([1, 2], gap="large")
confusion = bundle["confusion"] or {"matrix": [[0, 0], [0, 0]]}
with c1:
    st.plotly_chart(
        charts.confusion_heatmap(confusion["matrix"], confusion.get("labels", ["Non-churn", "Churn"])),
        width="stretch", config={"displayModeBar": False},
    )
    tn, fp, fn, tp = [confusion["matrix"][r][c] for r in range(2) for c in range(2)]
    st.caption(f"Test-set confusion at threshold {fmt_percent(threshold, 1)} — TN {tn} · FP {fp} · FN {fn} · TP {tp}")

with c2:
    leaderboard = bundle["leaderboard"] or []
    body = "".join(
        (
            "<tr" + (" style='background:rgba(16,185,129,.09)'" if i == 0 else "") + ">"
            f"<td class='mono'>{'★ ' if i == 0 else ''}{i + 1}</td>"
            f"<td style='font-weight:600;color:#F9FAFB'>{r.get('model', '—')}</td>"
            f"<td align='right' class='mono'>{r.get('cv_roc_auc', 0):.4f}</td>"
            f"<td align='right' class='mono'>{r.get('cv_f1', 0):.4f}</td>"
            f"<td align='right' class='mono'>{r.get('cv_accuracy', 0):.4f}</td>"
            f"<td align='right' class='mono'>{r.get('training_time_seconds', 0):.1f}s</td>"
            "<td>" + ("<span class='cap-badge'>tuned</span>" if r.get("tuned") else "<span class='pill-outline'>default</span>") + "</td>"
            "</tr>"
        )
        for i, r in enumerate(leaderboard)
    )
    st.markdown(
        """
        <div class="glass-panel" style="padding:.6rem 1rem">
        <table style="width:100%;border-collapse:collapse;font-size:.84rem">
        <thead><tr style="color:#9CA3AF;font-size:.68rem;text-transform:uppercase;letter-spacing:.06em">
          <td>#</td><td>Model</td><td align="right">ROC-AUC</td><td align="right">F1</td>
          <td align="right">Acc</td><td align="right">Fit (s)</td><td>Tuning</td>
        </tr></thead><tbody>""" + body + "</tbody></table></div>",
        unsafe_allow_html=True,
    )

# ---- Feature importance + learning curve ----------------------------------------------
section_title("Feature effects & learning behaviour")
c1, c2 = st.columns(2, gap="large")
importance = bundle["importance"] or {}
shap_imp = importance.get("shap", {}) or {}
items = shap_imp.get("importances") or stats.permutation_importance_items(importance)
with c1:
    st.markdown("**Global feature importance (mean |SHAP|)**")
    st.plotly_chart(
        charts.feature_importance_bars(list(items), top=14, sign_colors=False),
        width="stretch", config={"displayModeBar": False},
    )
with c2:
    st.markdown("**Learning curve — fraction of training data**")
    lc = _learning_curve()
    fig = charts.learning_curve(lc["train"], lc["validation"])
    fig.update_layout(xaxis=dict(tickmode="array", tickvals=list(range(len(lc["labels"]))), ticktext=lc["labels"]))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# ---- Training snapshot -------------------------------------------------------------------
section_title("Training snapshot")
stat_tiles(
    [
        ("Algorithm", model_label),
        ("Run", str((meta.get("run_id") or "—"))[:8]),
        ("Dataset", f"{meta.get('n_rows', '—')} rows"),
        ("Features", str(meta.get("n_features", "—"))),
        ("Trained", str((meta.get("trained_at") or "—"))[:10]),
        ("Threshold", fmt_percent(threshold, 1)),
    ]
)
st.caption(
    f"Dataset: {meta.get('dataset', 'telco_churn.csv')} · test split 20% · seed 42 · "
    f"python {meta.get('python', '—')}"
)