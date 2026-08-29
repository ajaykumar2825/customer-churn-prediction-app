"""Page 2 — Segment Analytics with an 11-facet filter sidebar."""

from __future__ import annotations

import streamlit as st

from components import charts
from components.layout import hero, insight_caption, section_title
from components.metric_cards import metric_row
from components.sidebar import analytics_filters, apply_filters, model_status_sidebar
from components.tables import segment_table
from utils import loader, stats
from utils.formatting import fmt_currency, fmt_number, fmt_percent

bundle = loader.load_model_bundle()
if bundle is None:
    st.stop()

model_status_sidebar(bundle)

hero(
    "Customer Analytics",
    "Slice the base with 11 simultaneous filters and see where churn concentrates — "
    "and the revenue attached to every segment.",
)
st.caption(
    "Filters: contract · internet · payment · gender · senior citizen · partner · dependents · "
    "paperless billing · tenure · monthly charges · total services"
)

data = loader.load_data()
scored = stats.scored_frame()

# ---- Sidebar filters -----------------------------------------------------------
state = analytics_filters(data)
filtered = apply_filters(scored, state)
n = len(filtered)

# ---- KPIs ----------------------------------------------------------------------
rollups = stats.segment_rollups(filtered)
m2m = rollups["contract"][0] if rollups["contract"] else {"churn_rate": 0.0}
rev_exposure = sum(r["expected_monthly_loss"] for r in rollups["contract"])
metric_row(
    [
        {
            "label": "Covered base",
            "value": fmt_number(n),
            "accent": "primary",
            "hint": "customers after filters",
        },
        {
            "label": "M-T-M share",
            "value": fmt_percent(m2m["customers"] / n, 1) if n else "0%",
            "accent": "danger",
            "hint": "month-to-month · top churn cohort",
        },
        {
            "label": "Revenue exposure",
            "value": fmt_currency(rev_exposure),
            "accent": "warning",
            "hint": "expected loss / mo within filter",
        },
    ]
)

# ---- Segment boards --------------------------------------------------------------
section_title("Segment deep dive — where churn concentrates")
dimension = st.radio(
    "Dimension",
    ["Contract", "Payment method", "Internet service", "Tenure cohort"],
    horizontal=True,
    label_visibility="collapsed",
)
dim_key = {
    "Contract": "contract",
    "Payment method": "payment_method",
    "Internet service": "internet_service",
    "Tenure cohort": "cohort",
}[dimension]
hints = {
    "contract": "Month-to-month is the single largest driver of churn.",
    "payment_method": "Electronic check correlates strongly with churn.",
    "internet_service": "Fiber-optic subscribers churn more — and carry the most revenue exposure.",
    "cohort": "Early-tenure customers are the most volatile segment.",
}
rows = rollups[dim_key]

col_left, col_right = st.columns([3, 2], gap="large")
with col_left:
    st.markdown(f"<p style='color:#9CA3AF;font-size:.84rem'>{hints[dim_key]}</p>", unsafe_allow_html=True)
    colours = [
        "#EF4444" if r["churn_rate"] > 33 else "#F59E0B" if r["churn_rate"] > 15 else "#10B981"
        for r in rows
    ]
    st.plotly_chart(
        charts.horizontal_bars([r["segment"] for r in rows], [r["churn_rate"] for r in rows], colours),
        width="stretch",
        config={"displayModeBar": False},
    )

with col_right:
    st.markdown('<div style="height:1.6rem"></div>', unsafe_allow_html=True)
    segment_table(rows)

# ---- Correlations / distributions -------------------------------------------------
section_title("Distributions & correlations")
c1, c2 = st.columns(2, gap="large")
with c1:
    st.markdown("**Monthly charges vs churn**")
    st.plotly_chart(charts.box_feature(filtered, "monthly_charges"), width="stretch",
                    config={"displayModeBar": False})
    st.markdown("**Tenure vs spend — charge intensity**")
    st.plotly_chart(charts.scatters(filtered), width="stretch", config={"displayModeBar": False})

with c2:
    st.markdown("**Tenure by outcome**")
    st.plotly_chart(charts.violin_feature(filtered, "tenure"), width="stretch",
                    config={"displayModeBar": False})
    st.markdown("**Feature correlation heatmap**")
    st.plotly_chart(
        charts.heatmap_corr(
            filtered,
            ["tenure", "monthly_charges", "total_charges", "avg_monthly_charge",
             "total_services", "senior_citizen", "paperless_billing"],
        ),
        width="stretch",
        config={"displayModeBar": False},
    )

# ---- Structure --------------------------------------------------------------------
section_title("Base structure")
s1, s2 = st.columns(2, gap="large")
with s1:
    st.markdown("**Contract hierarchy**")
    st.plotly_chart(charts.treemap_contract(filtered), width="stretch", config={"displayModeBar": False})
with s2:
    st.markdown("**Internet × payment**")
    st.plotly_chart(charts.sunburst_services(filtered), width="stretch", config={"displayModeBar": False})

# ---- Downloads ---------------------------------------------------------------------
st.divider()
dl = filtered[["customer_id", *[c for c in ["tenure", "monthly_charges", "total_charges", "contract",
                                            "internet_service", "payment_method", "total_services",
                                            "churn_probability", "churn"]]]]
st.download_button(
    "Export filtered CSV",
    data=dl.to_csv(index=False).encode("utf-8"),
    file_name="churn_segments.csv",
    mime="text/csv",
    use_container_width=False,
)

insight_caption(
    "Key insight",
    f"Of the <b>{fmt_number(n)}</b> filtered customers, the highest-risk segment carries "
    f"<b>{fmt_percent(rows[0]['churn_rate'] / 100, 1)}</b> predicted churn with "
    f"<b>{fmt_currency(rows[0]['expected_monthly_loss'])}/mo</b> at risk. A migration play off "
    "month-to-month terms compresses churn structurally.",
    danger=rows[0]["churn_rate"] > 33,
)