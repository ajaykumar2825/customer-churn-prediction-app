"""Page 7 — About the project."""

from __future__ import annotations

import streamlit as st

from components.layout import hero, section_title, stat_tiles
from components.sidebar import model_status_sidebar
from utils import loader
from utils.formatting import fmt_percent

bundle = loader.load_model_bundle()
if bundle is None:
    st.stop()

model_status_sidebar(bundle)
meta = bundle["meta"] or {}
metrics = bundle["metrics"] or {}
threshold = float((bundle["threshold"] or {}).get("threshold", 0.5))

hero(
    "About this project",
    "An end-to-end customer churn intelligence platform — trained, explained and deployed "
    "as a single Streamlit application.",
)

c1, c2 = st.columns([3, 2], gap="large")

with c1:
    section_title("The problem")
    st.markdown(
        """
        Churn silently erodes telecom revenue. This platform turns subscriber records into a
        ranked, probability-scored view of who is most likely to leave — then explains *why*
        and attaches a dollar amount to every decision.

        Features delivered:
        - **20 engineered features** from raw account data (service add-ons, tenure windows,
          average spend, contract & billing signals).
        - **Gradient-boosted champion** tuned with Optuna over 25 trials per model, compared
          against six other candidates on a stratified held-out split.
        - **SHAP explainability** at both scales: global feature effects and per-customer
          waterfall decomposition with plain-English narratives.
        - **Business layer**: revenue-at-risk, LTV, campaign ROI and a contract-migration play.
        """,
    )

    section_title("Architecture")
    st.markdown(
        """
        ```
        main.py  ── one Streamlit entrypoint
          ├── pages/        7 product pages (navigation)
          ├── components/   layout, filters, charts, cards, tables
          ├── utils/        loaders, preprocessing, prediction, explain, stats, reports
          ├── ml_pipeline/  training + evaluation + SHAP + business analytics
          ├── models/       persisted artifacts (joblib + json + shap pngs)
          ├── data/         telco_churn.csv
          └── reports/      generated HTML report snapshots
        ```
        Runs on Streamlit Community Cloud with `streamlit run main.py`; every model is
        cached with `@st.cache_resource`, SHAP imports lazily.
        """,
    )

with c2:
    section_title("Model card")
    champ = meta.get("model_label") or meta.get("model") or "xgboost"
    stat_tiles(
        [
            ("Algorithm", champ),
            ("Data", f"{meta.get('n_rows', '—')} rows"),
            ("Features", str(meta.get('n_features', '—'))),
            ("ROC-AUC", f"{metrics.get('roc_auc', 0):.4f}"),
            ("F1", f"{metrics.get('f1', 0):.4f}"),
            ("Threshold", fmt_percent(threshold, 1)),
        ]
    )
    st.markdown(
        f"""
        Trained `{meta.get('trained_at', '—')}` · python `{meta.get('python', '—')}` ·
        sklearn `{meta.get('packages', {}).get('sklearn', '—')}` · pandas
        `{meta.get('packages', {}).get('pandas', '—')}` · numpy
        `{meta.get('packages', {}).get('numpy', '—')}`   · dataset `{meta.get('dataset', 'telco_churn.csv')}`
        """,
    )

    section_title("Methodology")
    st.markdown(
        """
        - **Cleaning**: numeric coercion, drop of blank total-charges rows (7,043 → 7,032).
        - **Modelling**: 5-fold stratified CV baseline, Optuna tuning, F1-optimised threshold.
        - **Evaluation**: ROC/PR, calibration, lift & gain, learning curves, permutation + SHAP
          importances.
        - **Risk bands**: low `p<0.5`, medium `0.5≤p<0.7`, high `p≥0.7`.
        """
    )

section_title("Feature catalogue")
features = loader.load_feature_metadata()
rows = "".join(
    (
        "<tr>"
        f"<td class='mono'>{name}</td>"
        f"<td>{spec.get('label', name)}</td>"
        f"<td align='right'><span class='pill-outline'>{spec.get('kind', '—')}</span></td>"
        f"<td class='mono' style='color:#AEB9C7'>{spec.get('options', '') if spec.get('kind') == 'enum' else ('≤ ' + str(spec.get('le', '')) if spec.get('kind') == 'int' and 'le' in spec else '≥ 0')}</td>"
        "</tr>"
    )
    for name, spec in features.items()
)
st.markdown(
    """
    <div class="glass-panel" style="padding:.6rem 1rem">
    <table style="width:100%;border-collapse:collapse;font-size:.84rem">
    <thead><tr style="color:#9CA3AF;font-size:.68rem;text-transform:uppercase;letter-spacing:.06em">
      <td>Feature</td><td>Label</td><td align="right">Kind</td><td align="right">Bounds</td>
    </tr></thead><tbody>""" + rows + "</tbody></table></div>",
    unsafe_allow_html=True,
)

section_title("Author")
try:
    author = st.secrets.get("app", {})
except Exception:
    author = {}
github = author.get("github", "https://github.com/your-handle")
linkedin = author.get("linkedin", "https://www.linkedin.com/in/your-handle")
st.markdown(
    f"""
    <div class="glass-panel">
      <b style="font-size:1.05rem">{author.get('owner', 'Build with care')}</b>
      <div style="color:#AEB9C7;font-size:.86rem;margin-top:.25rem">
        {author.get('company', 'Retention Analytics')} · <a href="{github}" style="color:#10B981">GitHub</a>
        · <a href="{linkedin}" style="color:#06B6D4">LinkedIn</a>
      </div>
      <p style="font-size:.84rem">Contact: <a href="mailto:{author.get('email', 'you@example.com')}"
      style="color:#AEB9C7">{author.get('email', 'you@example.com')}</a></p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    "Churn Intelligence · Built with XGBoost + SHAP + Streamlit — © 2026 Retention Analytics · "
    "MIT licence"
)