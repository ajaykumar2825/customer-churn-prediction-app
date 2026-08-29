"""Table renderers: styled dataframes and HTML segment rows."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.formatting import churn_pct_badge, fmt_currency, fmt_number

PREDICTED_FEATURES = [
    ("customer_id", "Customer"),
    ("tenure", "Tenure"),
    ("monthly_charges", "Monthly $"),
    ("contract", "Contract"),
    ("internet_service", "Internet"),
    ("payment_method", "Payment"),
    ("total_services", "Services"),
    ("churn_probability", "Risk"),
]


def pretty_df(frame: pd.DataFrame, columns: dict | None = None) -> pd.DataFrame:
    return frame.copy()


def segment_table(rows: list[dict]) -> None:
    """HTML table of a segment rollup with churn badges and revenue bars."""
    max_loss = max((r["expected_monthly_loss"] for r in rows), default=1) or 1
    rows_html = []
    for r in rows:
        frac = max(2.0, r["expected_monthly_loss"] / max_loss * 100)
        bar = (
            '<div style="flex:1;height:10px;background:#1E293B;border-radius:99px;overflow:hidden">'
            f'<div style="height:100%;width:{frac:.1f}%;border-radius:99px;'
            'background:linear-gradient(90deg,#F59E0B,#EF4444)"></div>'
            "</div>"
        )
        rows_html.append(
            "<tr>"
            f"<td style='font-weight:600;color:#F9FAFB'>{r['segment']}</td>"
            f"<td align='right' class='mono'>{fmt_number(r['customers'])}</td>"
            f"<td align='right'>{churn_pct_badge(r['churn_rate'])}</td>"
            f"<td align='right' class='mono'>{fmt_number(r['predicted_churners'])}</td>"
            f"<td align='right' class='mono'>{fmt_currency(r['expected_monthly_loss'])}</td>"
            "</tr>"
            "<tr>"
            '<td colspan="5" style="padding:.1rem 0 .8rem">'
            '<div style="display:flex;align-items:center;gap:.6rem">'
            f'<span class="mono" style="font-size:.7rem;color:#9CA3AF">{_short(r["segment"])}</span>'
            f"{bar}"
            f'<span class="mono" style="font-size:.7rem;color:#AEB9C7">{fmt_currency(r["expected_monthly_loss"])}</span>'
            "</div>"
            "</td>"
            "</tr>"
        )
    body = "".join(rows_html)
    st.markdown(
        f"""
        <div class="glass-panel" style="padding:.6rem 1rem">
        <table style="width:100%;border-collapse:collapse;font-size:.86rem">
        <thead><tr style="color:#9CA3AF;font-size:.7rem;text-transform:uppercase;letter-spacing:.06em">
          <td>Segment</td><td align="right">Customers</td><td align="right">Churn %</td>
          <td align="right">Churners</td><td align="right">Loss / mo</td>
        </tr></thead><tbody>{body}</tbody></table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _short(name: str) -> str:
    return name if len(name) <= 14 else name[:12] + "…"


def data_table(frame: pd.DataFrame, column_config: dict | None = None, height: int = 380) -> None:
    st.dataframe(
        frame.reset_index(drop=True),
        width="stretch",
        hide_index=True,
        height=height,
        column_config=column_config,
    )