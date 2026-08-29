"""Page 1 — Command Center / Overview."""

from __future__ import annotations

import streamlit as st
import plotly.subplots as sp

from components import charts
from components.layout import insight_caption, hero, section_title
from components.metric_cards import metric_row
from utils import loader, stats
from utils.formatting import fmt_currency, fmt_number, fmt_percent, badge, risk_color

hero(
    "Churn Intelligence for Telco",
    "Command center for the customer base — churn exposure, cohort revenue and the "
    "highest-risk accounts, scored live by the gradient-boosted champion.",
    meta='<span class="cap-badge">v1.0.0</span>',
)

bundle = loader.load_model_bundle()
if bundle is None:
    st.error("Model bundle unavailable. Check the error above.")
    st.stop()

meta = bundle["meta"] or {}
scored = stats.scored_frame()
cohorts = stats.tenure_cohorts(scored)
split = stats.risk_split(scored)
expo = stats.exposure(scored, bundle["threshold"]["threshold"])
model_label = (meta.get("model_label") or meta.get("model") or "xgboost").title()

# ---- KPIs -------------------------------------------------------------------
churn_observed = float(scored["churn"].mean())
metric_row(
    [
        {
            "label": "Customer base",
            "value": fmt_number(len(scored)),
            "accent": "primary",
            "hint": "active cohort",
            "delta": "7060 retained",
        },
        {
            "label": "Churn rate",
            "value": fmt_percent(churn_observed, 1),
            "accent": "danger",
            "hint": "observed · held-out base",
            "delta": f"{fmt_number(expo['at_risk_customers'])} at risk",
        },
        {
            "label": "Revenue at risk",
            "value": fmt_currency(expo["expected_monthly_loss"]),
            "accent": "warning",
            "hint": "probability-weighted exposure / mo",
            "delta": f"{fmt_percent(expo['percent_at_risk'] / 100, 1)} of MRR",
        },
        {
            "label": "Retention score",
            "value": fmt_percent(1 - churn_observed, 1),
            "accent": "success",
            "hint": "share expected to stay",
            "delta": f"mean p {fmt_percent(expo['mean_probability'], 1)}",
        },
    ]
)

# ---- Charts ------------------------------------------------------------------
col1, col2 = st.columns([3, 2], gap="large")
with col1:
    section_title("Revenue & churn by tenure")
    rev = charts.area_revenue(cohorts, "cohort", "revenue", color=charts.PALETTE["blue"])
    churn = charts.area_revenue(cohorts, "cohort", "churned", color=charts.PALETTE["danger"])
    fig = sp.make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05)
    for trace in rev.data:
        fig.add_trace(trace, row=1, col=1)
    for trace in churn.data:
        fig.add_trace(trace, row=2, col=1)
    fig.update_layout(showlegend=False, height=420)
    fig.update_yaxes(title_text="Monthly revenue ($)", row=1, col=1)
    fig.update_yaxes(title_text="Churn events", row=2, col=1)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

with col2:
    section_title("Risk distribution")
    st.plotly_chart(
        charts.donut_risk(split, "Customers", fmt_number(len(scored))),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.markdown(
        f"""
        <div class="glass-panel inset" style="margin-top:.6rem">
          <div style="display:flex;justify-content:space-between;font-size:.84rem;color:#AEB9C7">
            <span>Predicted churners <b style="color:#EF4444">{fmt_number(expo['at_risk_customers'])}</b></span>
            <span>Dataset rows <b style="color:#F9FAFB">{fmt_number(len(scored))}</b></span>
            <span>Features <b style="color:#F9FAFB">20</b></span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---- Priority watchlist --------------------------------------------------------
section_title("Priority watchlist")
wl = stats.watchlist(scored)
rows = "".join(
    (
        '<div class="factor-row">'
        f'<span class="mono" style="color:#F9FAFB;font-weight:650">{r["customer_id"]}</span>'
        f'<span style="color:#9CA3AF;font-size:.78rem">{r["contract"]} · {r["payment_method"]}</span>'
        f'<span class="mono" style="color:#AEB9C7">${r["monthly_charges"]:.2f}/mo</span>'
        f'{badge(r["churn_probability"])}'
        "</div>"
    )
    for _, r in wl.iterrows()
)
st.markdown(f'<div class="glass-panel">{rows}</div>', unsafe_allow_html=True)
st.caption(
    f"Ranks by predicted probability · champion `{model_label}` · threshold "
    f"{fmt_percent(bundle['threshold']['threshold'], 1)} · trained {meta.get('trained_at', '—')[:10]}"
)

# ---- Banner ---------------------------------------------------------------------
insight_caption(
    "Retention is a revenue strategy",
    f"Over <b>{fmt_currency(expo['expected_annual_loss'])}</b> in annual revenue is exposed across the base. "
    "A targeted campaign recovers most of it for pennies on the dollar — open the Retention Strategy page "
    "for the economics.",
)