"""Prediction result card: gauge, badges, revenue impact, factory factors."""

from __future__ import annotations

import streamlit as st

from components.charts import gauge_value
from utils.formatting import badge, fmt_currency, fmt_percent, pretty, risk_color


def risk_summary(probability: float, threshold: float, model: str, monthly: float) -> None:
    p = float(probability)
    colour = risk_color(p)
    st.markdown(
        f"""
        <div class="glass-panel" style="margin-bottom:.8rem">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div>
              <div style="color:#9CA3AF;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase">Churn probability</div>
              <div style="font-size:2.4rem;font-weight:750;color:{colour};font-variant-numeric:tabular-nums">
                {fmt_percent(p, 1)}</div>
              {badge(p)}
            </div>
            <div style="text-align:right;color:#9CA3AF;font-size:.78rem">
              <div>threshold <b style="color:#F9FAFB">{fmt_percent(threshold, 1)}</b></div>
              <div style="margin-top:.3rem">{pretty(model)}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_gauge(probability: float) -> None:
    st.plotly_chart(gauge_value(probability), width="stretch", config={"displayModeBar": False})


def revenue_impact(probability: float, monthly: float, threshold: float, at_risk_label: str = "At risk monthly") -> None:
    expected_loss = float(probability) * float(monthly)
    colour = risk_color(float(probability))
    st.markdown(
        f"""
        <div class="glass-panel">
          <div style="color:#9CA3AF;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:.5rem">
            Revenue impact · threshold {fmt_percent(threshold, 1)}</div>
          <div style="display:flex;gap:12px">
            <div class="stat-tile" style="flex:1">
              <div class="cap">At risk monthly</div>
              <div class="val" style="color:{colour}">{fmt_currency(expected_loss)}</div>
            </div>
            <div class="stat-tile" style="flex:1">
              <div class="cap">Monthly charges</div>
              <div class="val">{fmt_currency(monthly)}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def factor_list(contributions: list[dict], limit: int = 6) -> None:
    rows = "".join(
        (
            '<div class="factor-row">'
            f'<span class="name">{c["feature"].replace("_", " · ")}</span>'
            f'<span class="val {"pos" if c["value"] >= 0 else "neg"}">{c["value"]:+.3f}</span>'
            "</div>"
        )
        for c in contributions[:limit]
    )
    st.markdown(
        f'<div class="glass-panel" style="padding:.7rem .9rem">{rows}</div>', unsafe_allow_html=True
    )


def narrative_panel(narrative: dict) -> None:
    summary = narrative.get("summary", "")
    factors = narrative.get("factors", [])
    lines = "<br>".join(f"• {f}" for f in factors)
    st.markdown(
        f"""
        <div class="insight-card">
          <div class="cap">Why — narrative</div>
          <p>{summary}</p>
          <p style="font-size:.84rem">{lines}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )