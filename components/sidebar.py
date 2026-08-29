"""Sidebar widgets: shared model status + the 11 analytics filters."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from utils import loader

DEFAULT_ENUMS = {
    "contract": ["Month-to-month", "One year", "Two year"],
    "internet_service": ["DSL", "Fiber optic", "No"],
    "payment_method": [
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)",
    ],
}


@st.cache_resource(show_spinner=False)
def _ranges(frame: pd.DataFrame) -> tuple:
    lo_tenure, hi_tenure = int(frame["tenure"].min()), int(frame["tenure"].max())
    lo_mrc, hi_mrc = float(frame["monthly_charges"].min()), float(frame["monthly_charges"].max())
    lo_ser, hi_ser = int(frame["total_services"].min()), int(frame["total_services"].max())
    return (lo_tenure, hi_tenure), (lo_mrc, hi_mrc), (lo_ser, hi_ser)


def model_status_sidebar(bundle: dict | None) -> None:
    st.sidebar.markdown("#### Model status")
    if bundle is None:
        st.sidebar.info("No trained model found. Enable auto-training.")
        return
    meta = bundle["meta"] or {}
    threshold = (bundle["threshold"] or {}).get("threshold", 0.5)
    metrics = bundle["metrics"] or {}
    st.sidebar.markdown(
        f"""
**Champion** — `{meta.get('model', 'unknown')}` · <span class="cap-badge">live</span>
""",
        unsafe_allow_html=True,
    )
    st.sidebar.caption(
        f"Trained {meta.get('trained_at', '—')[:10]}  ·  {meta.get('n_rows', '—')} rows"
    )
    st.sidebar.caption(f"Threshold `{threshold:.3f}`  ·  ROC-AUC `{metrics.get('roc_auc', 0):.4f}`")
    st.sidebar.divider()


@dataclass
class FilterState:
    contract: list[str]
    internet_service: list[str]
    payment_method: list[str]
    gender: list[str]
    senior_citizen: str
    partner: str
    dependents: str
    paperless_billing: str
    tenure_range: tuple[int, int]
    monthly_range: tuple[float, float]
    services_range: tuple[int, int]


def analytics_filters(frame: pd.DataFrame) -> FilterState:
    """Render the 11-facet sidebar and return the current selection state."""
    st.sidebar.markdown("#### Segment filters")
    (lt0, lt1), (mr0, mr1), (sr0, sr1) = _ranges(frame)

    contract = st.sidebar.multiselect("Contract", DEFAULT_ENUMS["contract"], default=DEFAULT_ENUMS["contract"])
    internet = st.sidebar.multiselect(
        "Internet service", DEFAULT_ENUMS["internet_service"], default=DEFAULT_ENUMS["internet_service"]
    )
    payment = st.sidebar.multiselect(
        "Payment method", DEFAULT_ENUMS["payment_method"], default=DEFAULT_ENUMS["payment_method"]
    )
    gender = st.sidebar.multiselect("Gender", ["Female", "Male"], default=["Female", "Male"])
    senior = st.sidebar.selectbox("Senior citizen", ["All", "Yes", "No"], index=0)
    partner = st.sidebar.selectbox("Has partner", ["All", "Yes", "No"], index=0)
    dependents = st.sidebar.selectbox("Has dependents", ["All", "Yes", "No"], index=0)
    paperless = st.sidebar.selectbox("Paperless billing", ["All", "Yes", "No"], index=0)
    tenure = st.sidebar.slider("Tenure (months)", lt0, lt1, (lt0, lt1), step=1)
    monthly = st.sidebar.slider("Monthly charges ($)", mr0, mr1, (mr0, mr1), step=5.0)
    services = st.sidebar.slider("Total services", sr0, sr1, (sr0, sr1), step=1)

    return FilterState(
        contract=list(contract),
        internet_service=list(internet),
        payment_method=list(payment),
        gender=list(gender),
        senior_citizen=senior,
        partner=partner,
        dependents=dependents,
        paperless_billing=paperless,
        tenure_range=tenure,
        monthly_range=monthly,
        services_range=services,
    )


@st.cache_data(show_spinner=False)
def apply_filters(frame: pd.DataFrame, f: FilterState) -> pd.DataFrame:
    """Apply the 11 facet filters onto the engineered frame."""

    def _yes_no(col: str, value: str) -> pd.Series:
        if value == "All":
            return pd.Series(True, index=frame.index)
        return frame[col].map(lambda v: "Yes" if v else "No").eq(value)

    mask = pd.Series(True, index=frame.index)
    mask &= frame["contract"].isin(f.contract)
    mask &= frame["internet_service"].isin(f.internet_service)
    mask &= frame["payment_method"].isin(f.payment_method)
    mask &= frame["gender_female"].map(lambda g: "Female" if g else "Male").isin(f.gender)
    mask &= _yes_no("senior_citizen", f.senior_citizen)
    mask &= _yes_no("partner", f.partner)
    mask &= _yes_no("dependents", f.dependents)
    mask &= _yes_no("paperless_billing", f.paperless_billing)
    mask &= frame["tenure"].between(*f.tenure_range)
    mask &= frame["monthly_charges"].between(*f.monthly_range)
    mask &= frame["total_services"].between(*f.services_range)
    return frame[mask].copy()