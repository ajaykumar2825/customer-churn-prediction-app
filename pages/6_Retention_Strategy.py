"""Page 6 — Business Strategy: exposure, CLV, campaign ROI, migration plays."""

from __future__ import annotations

import streamlit as st

from components import charts
from components.layout import hero, insight_caption, section_title
from components.metric_cards import metric_row
from components.sidebar import model_status_sidebar
from components.tables import segment_table
from utils import loader, stats
from utils.formatting import fmt_currency, fmt_number, fmt_percent

bundle = loader.load_model_bundle()
if bundle is None:
    st.stop()

model_status_sidebar(bundle)
threshold = float((bundle["threshold"] or {}).get("threshold", 0.5))

hero(
    "Retention Strategy",
    "Turn model output into revenue decisions — exposure, CLV, campaign ROI and the "
    "contract-migration play that compresses churn structurally.",
)

scored = stats.scored_frame()
expo = stats.exposure(scored, threshold)
campaign = stats.campaign_economics(scored)
rollups = stats.segment_rollups(scored)
tenure_rows = rollups["cohort"]
cli = float(scored["total_charges"].mean())

metric_row(
    [
        {
            "label": "Annual revenue at risk",
            "value": fmt_currency(expo["expected_annual_loss"]),
            "accent": "danger",
            "hint": f"{fmt_percent(expo['percent_at_risk'] / 100, 1)} of MRR exposed",
        },
        {
            "label": "Expected monthly loss",
            "value": fmt_currency(expo["expected_monthly_loss"]),
            "accent": "warning",
            "hint": f"{fmt_number(expo['at_risk_customers'])} at-risk customers",
        },
        {
            "label": "Avg customer LTV",
            "value": fmt_currency(cli),
            "accent": "primary",
            "hint": "lifetime charges retained",
        },
        {
            "label": "Campaign ROI",
            "value": f"{campaign['roi']:.1f}×",
            "accent": "success",
            "hint": f"{fmt_number(campaign['saved'])} estimated saved",
        },
    ]
)

# ---- Contract migration play ----------------------------------------------------------
section_title("Contract migration play")
contract_impact = (bundle.get("strategy") or {}).get("contract_impact") or {}
if contract_impact:
    current = contract_impact.get("current_avg_churn", 0.0)
    hypoth = contract_impact.get("hypothetical_avg_churn_after_contract", 0.0)
    scale = 45.0
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("**Average churn rate today**")
        st.markdown(
            f"""
            <div style="margin:.5rem 0 1.2rem">
              <div style="display:flex;align-items:center;gap:.8rem">
                <span class="mono" style="color:#EF4444;font-weight:700;font-size:1.4rem">{current:.1f}%</span>
                <div style="flex:1;height:16px;background:#1E293B;border-radius:99px;overflow:hidden">
                <div style="height:100%;width:{current / scale * 100:.1f}%;border-radius:99px;
                background:linear-gradient(90deg,rgba(239,68,68,.7),#EF4444)"></div></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**After migration**")
        st.markdown(
            f"""
            <div style="margin:.5rem 0 1.2rem">
              <div style="display:flex;align-items:center;gap:.8rem">
                <span class="mono" style="color:#10B981;font-weight:700;font-size:1.4rem">{hypoth:.1f}%</span>
                <div style="flex:1;height:16px;background:#1E293B;border-radius:99px;overflow:hidden">
                <div style="height:100%;width:{hypoth / scale * 100:.1f}%;border-radius:99px;
                background:linear-gradient(90deg,rgba(16,185,129,.7),#10B981)"></div></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown("**Contract mix**")
        shares = [
            ("month_to_month_share", "MTM", "#EF4444"),
            ("one_year_share", "1y", "#F59E0B"),
            ("two_year_share", "2y", "#10B981"),
        ]
        bars = "".join(
            (
                f'<div style="margin:.6rem 0"><div style="display:flex;justify-content:space-between;'
                f'font-size:.78rem;color:#AEB9C7"><span>{label}</span>'
                f'<span class="mono">{contract_impact.get(key, 0):.1f}%</span></div>'
                f'<div style="height:10px;background:#1E293B;border-radius:99px;overflow:hidden;margin-top:.25rem">'
                f'<div style="height:100%;width:{contract_impact.get(key, 0) / 100 * 100:.1f}%;'
                f'background:{colour}"></div></div></div>'
            )
            for key, label, colour in shares
        )
        st.markdown(f'<div class="glass-panel inset">{bars}</div>', unsafe_allow_html=True)
        st.caption(contract_impact.get("impact_note", ""))

# ---- Campaign economics ------------------------------------------------------------------
section_title("Retention campaign economics")
st.caption("One-shot outbound campaign on p ≥ 0.6 at $35/contact and a 35% save rate")
k1, k2, k3, k4 = st.columns(4, gap="large")
stats_html = [
    (k1, "Targeted", fmt_number(campaign["targeted"]), "#EF4444"),
    (k2, "Estimated saved", fmt_number(campaign["saved"]), "#10B981"),
    (k3, "Campaign cost", fmt_currency(campaign["cost"]), "#F9FAFB"),
    (k4, "Recovered / yr", fmt_currency(campaign["recovered_annual"]), "#06B6D4"),
]
for col, label, value, colour in stats_html:
    with col:
        st.markdown(
            f'<div class="glass-panel" style="text-align:center;padding:1.1rem .5rem">'
            f'<div style="font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:#9CA3AF">{label}</div>'
            f'<div class="mono" style="font-size:1.7rem;font-weight:750;color:{colour};margin-top:.3rem">{value}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
st.markdown(
    f"""
    <div class="glass-panel inset" style="display:flex;align-items:center;justify-content:space-between;margin-top:.6rem">
      <div>
        <div style="color:#9CA3AF;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase">Return on retention spend</div>
        <div style="font-size:.9rem;color:#AEB9C7;margin-top:.2rem">
          Every dollar spent on outreach is projected to return {campaign['roi']:.1f} dollars in retained
          MRR over the following year.</div>
      </div>
      <div class="mono" style="font-size:2.6rem;font-weight:750;color:#10B981">{campaign['roi']:.1f}×</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- Where churn concentrates ----------------------------------------------------------------
section_title("Where churn concentrates")
c1, c2 = st.columns([3, 2], gap="large")
with c1:
    st.markdown("**Tenure cohorts ranked by churn rate**")
    colours = [
        "#EF4444" if r["churn_rate"] > 33 else "#F59E0B" if r["churn_rate"] > 15 else "#10B981"
        for r in tenure_rows
    ]
    st.plotly_chart(
        charts.horizontal_bars([r["segment"] for r in tenure_rows], [r["churn_rate"] for r in tenure_rows], colours),
        width="stretch", config={"displayModeBar": False},
    )
with c2:
    st.markdown("**Segment exposure**")
    segment_table(tenure_rows)

worst = tenure_rows[0] if tenure_rows else {}
insight_caption(
    "Highest-leverage cohort",
    f"<b>{worst.get('segment', '—')}</b> — <b style='color:#EF4444'>{worst.get('churn_rate', 0):.1f}%</b> churn, "
    f"<b>{fmt_currency(worst.get('expected_monthly_loss', 0))}/mo</b> at risk. Prioritise this cohort and the "
    "contract-migration play to compress churn structurally.",
    danger=True,
)

# ---- Executive summary -----------------------------------------------------------------------
_summary = (
    f"The model identifies <b>{fmt_number(expo['at_risk_customers'])} customers</b> "
    f"(p≥{fmt_percent(threshold, 1)}) carrying <b>{fmt_currency(expo['expected_annual_loss'])}</b> of annual "
    f"revenue exposure. Month-to-month contracts, electronic-check payment and fiber-optic service are the "
    "strongest risk markers; new customers in their first twelve months are the most volatile cohort. "
    f"A <b>{fmt_currency(campaign['cost'])}</b> one-shot outreach campaign is projected to preserve around "
    f"<b>{fmt_currency(campaign['recovered_annual'])}</b> of that revenue — a <b>{campaign['roi']:,.1f}×</b> "
    f"return. Prioritise the <b>{worst.get('segment', 'early-tenure')}</b> cohort and the contract-migration "
    "play to compress churn structurally."
)
insight_caption("Executive summary", _summary)