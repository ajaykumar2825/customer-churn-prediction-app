"""Churn Intelligence — Streamlit entry point.

Single deployable app: ``streamlit run main.py``.
"""

from __future__ import annotations

import streamlit as st

from components.layout import inject_global_css, render_topbar

NAV_PAGES = [
    st.Page("pages/1_Overview.py", title="Overview", icon=":material/space_dashboard:", default=True),
    st.Page("pages/2_Customer_Analytics.py", title="Customer Analytics", icon=":material/query_stats:"),
    st.Page("pages/3_Predict_Churn.py", title="Predict Churn", icon=":material/auto_awesome:"),
    st.Page("pages/4_Model_Performance.py", title="Model Performance", icon=":material/speed:"),
    st.Page("pages/5_SHAP_Explainability.py", title="SHAP Explainability", icon=":material/manage_search:"),
    st.Page("pages/6_Retention_Strategy.py", title="Retention Strategy", icon=":material/savings:"),
    st.Page("pages/7_About_Project.py", title="About Project", icon=":material/account_circle:"),
]

st.set_page_config(
    page_title="Churn Intelligence",
    page_icon="assets/icons/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

pg = st.navigation(NAV_PAGES, position="sidebar")
render_topbar()
pg.run()

st.markdown(
    """
    <style>
    footer{visibility:visible!important;padding:2rem 0 .5rem;text-align:center}
    footer:before{content:"Churn Intelligence · Built with XGBoost + SHAP + Streamlit — © 2026 Retention Analytics";color:#64748B;font-size:.72rem}
    </style>
    """,
    unsafe_allow_html=True,
)