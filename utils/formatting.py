"""Formatting helpers for currencies, numbers, percentages and badges."""

from __future__ import annotations

import html


def fmt_currency(value: float, digits: int = 0) -> str:
    return f"${value:,.{digits}f}"


def fmt_number(value) -> str:
    return f"{int(value):,}"


def fmt_percent(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def pretty(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


RISK_COLORS = {"low": "#10B981", "medium": "#F59E0B", "high": "#EF4444"}


def risk_color(prob: float) -> str:
    if prob >= 0.7:
        return "#EF4444"
    if prob >= 0.5:
        return "#F59E0B"
    return "#10B981"


def badge(probability: float, label: str | None = None, mono: bool = False) -> str:
    """Capsule risk badge with a dot and UPPERCASE label."""
    pct = round(probability * 100)
    colour = risk_color(probability)
    text = label or ("KEEP" if probability < 0.5 else "CHURN")
    mono_cls = "mono" if mono else ""
    return (
        f'<span class="risk-badge {mono_cls}" style="color:{colour};'
        f"border-color:{colour}33;background:{colour}1a;"
        f'"><span class="dot" style="background:{colour}"></span>{html.escape(text.upper())}&nbsp;{pct}%</span>'
    )


def churn_pct_badge(churn_rate: float) -> str:
    """Semantic badge for a segment churn rate."""
    colour = "#EF4444" if churn_rate > 33 else "#F59E0B" if churn_rate > 15 else "#10B981"
    return (
        f'<span class="churn-badge mono" style="color:{colour};border-color:{colour}33;'
        f'background:{colour}1a;">{churn_rate:.1f}%</span>'
    )


def kpi_card(label: str, value: str, accent: str, hint: str = "", delta: str | None = None) -> str:
    """Glass KPI card with a small icon chip."""
    chips = {
        "primary": "from-primary/25 to-primary/5 text-primary",
        "cyan": "from-cyan/25 to-cyan/5 text-cyan",
        "success": "from-success/25 to-success/5 text-success",
        "warning": "from-warning/25 to-warning/5 text-warning",
        "danger": "from-danger/25 to-danger/5 text-danger",
    }
    chip_cls = chips.get(accent, chips["primary"])
    delta_html = ""
    if delta:
        delta_html = f'<div class="kpi-delta">{delta}</div>'
    return (
        f'<div class="metric-card"><div class="metric-chip gradient {chip_cls}"></div>'
        f'<span class="label">{html.escape(label)}</span>'
        f'<div class="value">{value}</div>{delta_html}'
        f'<div class="hint">{html.escape(hint)}</div></div>'
    )


def glass_panel(inner: str, extra: str = "") -> str:
    return f'<div class="glass-panel {extra}">{inner}</div>'