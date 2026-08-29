"""KPI metric rows rendered as premium glass cards."""

from __future__ import annotations

import streamlit as st

from utils.formatting import kpi_card


def metric_row(cards: list[dict], columns: int | None = None) -> None:
    """Render a row of metric-card definitions.

    Each card: {"label", "value", "accent", "hint", "delta"?}
    """
    col_cls = {3: "c3", 5: "c5"}.get(columns or len(cards), "")
    body = "".join(
        kpi_card(
            c["label"],
            c["value"],
            c.get("accent", "primary"),
            c.get("hint", ""),
            c.get("delta"),
        )
        for c in cards
    )
    st.markdown(f'<div class="metric-row {col_cls}">{body}</div>', unsafe_allow_html=True)