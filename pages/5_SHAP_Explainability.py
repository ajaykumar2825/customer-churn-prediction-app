"""Page 5 — Explainability Lab: global SHAP + per-customer local factors."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from components import charts
from components.layout import hero, insight_caption, section_title, stat_tiles
from components.prediction_card import factor_list, narrative_panel
from components.sidebar import model_status_sidebar
from ml_pipeline.config import DEFAULT_SHAP_DIR
from utils import loader, stats
from utils.formatting import fmt_currency, fmt_percent

bundle = loader.load_model_bundle()
if bundle is None:
    st.stop()

model_status_sidebar(bundle)
threshold = float((bundle["threshold"] or {}).get("threshold", 0.5))

hero(
    "Explainability Lab",
    "Exactly why the model flags any customer — the global SHAP summary, then live "
    "waterfall explanations for the highest-risk profiles in the base.",
)

# ---- Global -------------------------------------------------------------------------
section_title("Global feature effects")
shap_global = bundle.get("shap_global") or {}
shap_items = shap_global.get("importances") or []
c1, c2 = st.columns([3, 2], gap="large")
with c1:
    st.markdown("**Mean |SHAP contribution| across the scored population**")
    if shap_items:
        st.plotly_chart(
            charts.feature_importance_bars(list(shap_items), top=15, sign_colors=False),
            width="stretch", config={"displayModeBar": False},
        )
    else:  # pragma: no cover
        st.info("No persisted global SHAP artefacts found — run a training job to generate them.")

with c2:
    st.markdown("**Global summary plots**")
    beeswarm = DEFAULT_SHAP_DIR / "shap_summary_beeswarm.png"
    bar = DEFAULT_SHAP_DIR / "shap_summary_bar.png"
    if beeswarm.exists():
        st.image(str(beeswarm), caption="SHAP beeswarm — feature value colour scale", width="stretch")
    else:
        st.caption("Beeswarm PNG not present in `models/shap/`.")
    if bar.exists():
        expander = st.expander("Bar summary")
        expander.image(str(bar), caption="Mean |SHAP| (precomputed)", width="stretch")
    if shap_global.get("expected_value") is not None:
        st.caption(
            f"Base (expected) value: {float(shap_global['expected_value']):+.3f} on the log-odds scale "
            f"· computed over {shap_global.get('n_rows', '—')} customers"
        )

# ---- Local ---------------------------------------------------------------------------
section_title("Local explanations — pick a customer")
scored = stats.scored_frame()
candidates = scored.sort_values("churn_probability", ascending=False).head(12)
options = [f"{r['customer_id']} · {round(r['churn_probability'] * 100)}%" for _, r in candidates.iterrows()]
key2id = {label: cid for label, cid in zip(options, candidates["customer_id"])}

col_pick, col_btn = st.columns([3, 1])
with col_pick:
    choice = st.selectbox("Customer", options, index=0)
with col_btn:
    st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)
    if st.button("Compare next ▸", width="stretch"):
        idx = options.index(choice)
        choice = options[(idx + 1) % len(options)]
        st.session_state["_shap_customer"] = choice

if "_shap_customer" in st.session_state:
    choice = st.session_state["_shap_customer"]

cid = key2id[choice]
row = scored.set_index("customer_id").loc[cid]
prob = float(row["churn_probability"])

col_left, col_right = st.columns([3, 2], gap="large")
with col_left:
    st.markdown(f"#### Why this prediction — {cid}")
    from utils.explainability import local_explanation

    with st.spinner("Computing SHAP…"):
        expl = local_explanation(bundle["classifier"], bundle["preprocessor"], row[:-1], prob, threshold)
    st.plotly_chart(charts.shap_waterfall(expl["contributions"]),
                    width="stretch", config={"displayModeBar": False})
    factor_list(expl["contributions"], limit=12)
    narrative_panel(expl["narrative"])

with col_right:
    st.markdown(f"#### Profile — {cid}")
    stat_tiles(
        [
            ("Tenure", f"{int(row['tenure'])} mo"),
            ("Monthly", fmt_currency(row["monthly_charges"], 2)),
            ("Total charges", fmt_currency(row["total_charges"], 2)),
            ("Services", str(int(row["total_services"]))),
            ("Contract", str(row["contract"])[:9]),
            ("Risk", fmt_percent(prob, 1)),
        ]
    )
    st.markdown(f"**Predicted churn probability · {fmt_percent(prob, 1)}**")
    st.plotly_chart(charts.gauge_value(prob), width="stretch", config={"displayModeBar": False})
    insight_caption(
        "Drivers",
        f"The dominant push factors are {', '.join('`' + c['feature'].replace('_', ' · ') + '`' for c in expl['contributions'][:3])} — "
        "the waterfall above shows exactly how each moves the odds.",
        danger=prob >= 0.5,
    )