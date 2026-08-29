"""Plotly chart builders for every dashboard page (dark theme)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

PALETTE = {
    "primary": "#10B981",
    "cyan": "#06B6D4",
    "blue": "#2563EB",
    "violet": "#8B5CF6",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "success": "#10B981",
    "muted": "#64748B",
    "grid": "rgba(148,163,184,0.08)",
}

RISK_COLORS = ["#10B981", "#F59E0B", "#EF4444"]

_BASE = {
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#E5E7EB", "family": "Inter, system-ui, sans-serif"},
    "colorway": list(PALETTE.values()),
}

pio.templates["churn"] = go.layout.Template(layout=_BASE)


def _finish(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        template="churn",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=11)),
        xaxis=dict(gridcolor=PALETTE["grid"], zeroline=False, linecolor="rgba(148,163,184,.2)"),
        yaxis=dict(gridcolor=PALETTE["grid"], zeroline=False, linecolor="rgba(148,163,184,.2)"),
        hoverlabel=dict(bgcolor="#111827", bordercolor="#1E293B", font=dict(color="#F9FAFB")),
    )
    return fig


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
def area_revenue(df: pd.DataFrame, x: str, y: str, color: str = PALETTE["blue"], height: int = 300) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=df[x], y=df[y], mode="lines",
            line=dict(color=color, width=2.5),
            fill="tozeroy",
            fillcolor=_opacity(color, 0.5),
        )
    )
    fig.update_traces(hovertemplate="%{y:$,.0f}")
    return _finish(fig, height)


def donut_risk(counts: dict[str, int], center_label: str, center_value: str, height: int = 310) -> go.Figure:
    labels = list(counts.keys())
    values = list(counts.values())
    fig = go.Figure(
        go.Pie(
            labels=labels, values=values, hole=0.62, sort=False,
            marker=dict(colors=RISK_COLORS[: len(labels)], line=dict(color="#09090B", width=3)),
            textinfo="label", textposition="outside",
            hovertemplate="%{label}<br>%{value:,} customers (%{percent})<extra></extra>",
        )
    )
    fig.add_annotation(
        text=f"<b>{center_value}</b><br><span style='font-size:10px;letter-spacing:.12em;"
        f"color:#9CA3AF'>{center_label.upper()}</span>",
        showarrow=False, font=dict(size=26, color="#F9FAFB"),
    )
    return _finish(fig, height)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
def horizontal_bars(labels: list[str], values: list[float], colors: list[str], height: int = 300) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=values, y=labels, orientation="h", marker_color=colors,
            marker_line=dict(width=0),
            hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(xaxis=dict(ticksuffix="%"), yaxis=dict(autorange="reversed"))
    return _finish(fig, height)


def heatmap_corr(frame: pd.DataFrame, cols: list[str], height: int = 400) -> go.Figure:
    corr = frame[cols].corr().round(2)
    fig = go.Figure(
        go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.columns,
            colorscale=[[0, "#0F172A"], [0.5, "#1E293B"], [1, "#10B981"]],
            zmid=0, xgap=2, ygap=2,
            hovertemplate="%{y} × %{x}: %{z}<extra></extra>",
        )
    )
    fig.update_layout(height=height)
    return _finish(fig, height)


def box_feature(frame: pd.DataFrame, y: str, color: str = PALETTE["cyan"], height: int = 260) -> go.Figure:
    fig = go.Figure(
        go.Box(
            x=frame["churn"].map({1: "Churned", 0: "Retained"}),
            y=frame[y], marker_color=color,
            boxmean=True, hovertemplate="%{x}<br>%{y:.0f}<extra></extra>",
        )
    )
    return _finish(fig, height)


def violin_feature(frame: pd.DataFrame, y: str, height: int = 260) -> go.Figure:
    fig = px.violin(
        frame, x="churn", y=y, color="churn", box=True, points=False,
        color_discrete_map={0: PALETTE["success"], 1: PALETTE["danger"]},
        labels={"churn": "", y: "value"},
    )
    return _finish(fig, height)


def scatters(frame: pd.DataFrame, height: int = 280) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=frame["tenure"], y=frame["monthly_charges"],
            mode="markers",
            marker=dict(color=frame["total_charges"], colorscale=[[0, "#0F172A"], [1, "#10B981"]],
                        size=5, opacity=0.7, colorbar=dict(title="$")),
            hovertemplate="tenure %{x} · $%{y}<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Tenure (months)", yaxis_title="Monthly charges ($)")
    return _finish(fig, height)


def sunburst_services(frame: pd.DataFrame, height: int = 340) -> go.Figure:
    df = frame.groupby(["internet_service", "payment_method"], observed=True)["customer_id"].count().reset_index(name="n")
    fig = px.sunburst(
        df, path=["internet_service", "payment_method"], values="n", color="n",
        color_continuous_scale=[[0, "#0F172A"], [0.6, "#2563EB"], [1, "#10B981"]],
    )
    fig.update_traces(hovertemplate="%{label}<br>%{value:,} customers<extra></extra>")
    return _finish(fig, height)


def treemap_contract(frame: pd.DataFrame, height: int = 340) -> go.Figure:
    df = (
        frame.groupby(["contract", "payment_method", "internet_service"], observed=True)["customer_id"]
        .count()
        .reset_index(name="customers")
    )
    fig = px.treemap(
        df, path=["contract", "payment_method", "internet_service"], values="customers", color="customers",
        color_continuous_scale=[[0, "#0F172A"], [0.6, "#2563EB"], [1, "#06B6D4"]],
    )
    fig.update_traces(hovertemplate="%{label}<br>%{value:,}<extra></extra>")
    return _finish(fig, height)


# ---------------------------------------------------------------------------
# Model performance
# ---------------------------------------------------------------------------
def roc_curve(fpr: list, tpr: list, auc: float, height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=PALETTE["muted"], dash="dash", width=1.5), name="Random")
    )
    fig.add_trace(
        go.Scatter(x=fpr, y=tpr, mode="lines", line=dict(color=PALETTE["blue"], width=3), name=f"Model (AUC {auc:.4f})",
                  fill="tozeroy", fillcolor=_opacity(PALETTE["blue"], 0.12))
    )
    fig.update_layout(xaxis_title="False positive rate", yaxis_title="True positive rate")
    return _finish(fig, height)


def pr_curve(precision: list, recall: list, auc: float, height: int = 300) -> go.Figure:
    fig = go.Figure(
        go.Scatter(x=recall, y=precision, mode="lines", line=dict(color=PALETTE["cyan"], width=3), name=f"Model (AP {auc:.3f})",
                  fill="tozeroy", fillcolor=_opacity(PALETTE["cyan"], 0.12))
    )
    fig.update_layout(xaxis_title="Recall", yaxis_title="Precision")
    return _finish(fig, height)


def threshold_curve(thresholds: np.ndarray, f1s: np.ndarray, accs: np.ndarray, recs: np.ndarray, best_t: float, height: int = 320) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=thresholds, y=f1s, name="F1", line=dict(color=PALETTE["primary"], width=2.5)))
    fig.add_trace(go.Scatter(x=thresholds, y=accs, name="Accuracy", line=dict(color=PALETTE["blue"], width=2)))
    fig.add_trace(go.Scatter(x=thresholds, y=recs, name="Recall", line=dict(color=PALETTE["warning"], width=2)))
    fig.add_vline(x=best_t, line_dash="dash", line_color=PALETTE["danger"], annotation_text=f"best {best_t:.3f}",
                 annotation_position="top right")
    fig.update_layout(xaxis_title="Threshold", yaxis_title="Score")
    return _finish(fig, height)


def lift_gain_curves(curves: dict, height: int = 300) -> tuple[go.Figure, go.Figure]:
    lift = go.Figure(
        go.Scatter(x=curves["lift"]["population_percent"], y=curves["lift"]["lift"],
                   mode="lines", line=dict(color=PALETTE["blue"], width=2.5),
                   fill="tozeroy", fillcolor=_opacity(PALETTE["blue"], 0.12))
    )
    lift.add_hline(y=1, line_dash="dash", line_color=PALETTE["muted"])
    lift.update_layout(xaxis_title="Population (%)", yaxis_title="Lift")

    gain = go.Figure(
        go.Scatter(x=curves["gain"]["population_percent"], y=curves["gain"]["gain"],
                   mode="lines", line=dict(color=PALETTE["violet"], width=2.5),
                   fill="tozeroy", fillcolor=_opacity(PALETTE["violet"], 0.12))
    )
    gain.update_layout(xaxis_title="Population (%)", yaxis_title="Cumulative gain")
    return _finish(lift, height), _finish(gain, height)


def calibration(prob_pred: list, prob_true: list, height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=PALETTE["muted"], dash="dash"), name="Perfectly calibrated")
    )
    fig.add_trace(
        go.Scatter(x=prob_pred, y=prob_true, mode="lines+markers", line=dict(color=PALETTE["warning"], width=2.5),
                   marker=dict(size=8), name="Model")
    )
    fig.update_layout(xaxis_title="Predicted probability", yaxis_title="Observed frequency")
    return _finish(fig, height)


def confusion_heatmap(matrix: list, labels: list, height: int = 300) -> go.Figure:
    fig = go.Figure(
        go.Heatmap(
            z=matrix, x=labels, y=labels,
            colorscale=[[0, "#0F172A"], [0.5, "#134E4A"], [1, "#10B981"]],
            text=np.array(matrix, dtype=object), texttemplate="%{text}",
            xgap=3, ygap=3,
            hovertemplate="%{y} → predicted %{x}: %{z}<extra></extra>",
        )
    )
    fig.update_layout(xaxis_title="Predicted", yaxis_title="Actual")
    return _finish(fig, height)


def feature_importance_bars(items: list[dict], top: int = 14, height: int = 340, sign_colors: bool = True) -> go.Figure:
    rows = items[:top]
    labels = [r["feature"].replace("_", " · ") for r in rows]
    values = [r["importance"] for r in rows]
    colors = []
    for v in values:
        if sign_colors:
            colors.append(PALETTE["danger"] if v >= 0 else PALETTE["success"])
        else:
            colors.append(PALETTE["primary"])
    fig = go.Figure(
        go.Bar(x=values, y=labels, orientation="h", marker_color=colors,
               marker_line=dict(width=0), hovertemplate="%{y}: %{x:.4f}<extra></extra>")
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return _finish(fig, height)


def learning_curve(train: list, validation: list, height: int = 300) -> go.Figure:
    fig = go.Figure()
    if train:
        fig.add_trace(go.Scatter(y=train, name="Train", line=dict(color=PALETTE["blue"], width=2.5)))
    if validation:
        fig.add_trace(go.Scatter(y=validation, name="Validation", line=dict(color=PALETTE["primary"], width=2.5)))
    fig.update_layout(xaxis_title="Iteration", yaxis_title="ROC-AUC")
    return _finish(fig, height)


def histogram(values: np.ndarray, color: str = PALETTE["primary"], height: int = 260) -> go.Figure:
    fig = go.Figure(
        go.Histogram(x=values, nbinsx=30, marker_color=color,
                     marker_line=dict(color="#09090B", width=1),
                     hovertemplate="%{x:.2f} · %{y} customers<extra></extra>")
    )
    fig.update_layout(xaxis_title="Churn probability", yaxis_title="Customers")
    return _finish(fig, height)


def gauge_value(probability: float, height: int = 200) -> go.Figure:
    colour = "#EF4444" if probability >= 0.7 else "#F59E0B" if probability >= 0.5 else "#10B981"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability,
            number={"suffix": "%", "valueformat": ".0f", "font": {"size": 40, "color": colour}},
            gauge={
                "axis": {"range": [0, 1], "tickformat": "%", "tickcolor": "#64748B"},
                "bar": {"color": colour, "thickness": 0.45},
                "steps": [
                    {"range": [0, 0.5], "color": "rgba(16,185,129,.15)"},
                    {"range": [0.5, 0.7], "color": "rgba(245,158,11,.15)"},
                    {"range": [0.7, 1], "color": "rgba(239,68,68,.15)"},
                ],
                "threshold": {
                    "line": {"color": "#F9FAFB", "width": 3},
                    "thickness": 0.9,
                    "value": 0.5,
                },
                "shape": "angular",
            },
        )
    )
    return _finish(fig, height)


def shap_waterfall(contributions: list[dict], height: int = 320) -> go.Figure:
    """Waterfall of signed SHAP contributions around the base value."""
    rows = [c for c in contributions if abs(c["value"]) > 1e-9][:10]
    labels = [r["feature"].replace("_", " · ") for r in rows]
    values = [r["value"] for r in rows]
    total = float(sum(values))
    fig = go.Figure(
        go.Waterfall(
            measure=["relative"] * len(values) + ["total"],
            x=labels + ["Cumulative"],
            y=values + [total],
            text=[f"{v:+.3f}" for v in values] + [f"{total:+.3f}"],
            textposition="outside",
            connector={"line": {"color": "#334155", "dash": "dot"}},
            increasing={"marker": {"color": PALETTE["danger"]}},
            decreasing={"marker": {"color": PALETTE["success"]}},
        )
    )
    fig.add_hline(y=0, line_color="#64748B", line_width=1)
    return _finish(fig, height)


def _opacity(hex_colour: str, alpha: float) -> str:
    r = int(hex_colour[1:3], 16)
    g = int(hex_colour[3:5], 16)
    b = int(hex_colour[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"