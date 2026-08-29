"""Page 3 — Prediction Studio: single profile + batch scoring."""

from __future__ import annotations

import io
import json

import pandas as pd
import streamlit as st

from components import charts
from components.layout import hero, section_title
from components.metric_cards import metric_row
from components.prediction_card import factor_list, narrative_panel, revenue_impact, risk_gauge
from components.sidebar import model_status_sidebar
from utils import loader, report_generator
from utils.formatting import fmt_currency, fmt_number, fmt_percent, pretty
from utils.preprocessing import DEFAULT_INPUT, coerce_uploaded_to_engineered, parse_jsonl, rows_to_engineered
from utils.prediction import batch_summary, score_frame, score_single

bundle = loader.load_model_bundle()
if bundle is None:
    st.error("Trained artifacts missing — the app needs `models/` populated (or auto-training).")
    st.stop()

model_status_sidebar(bundle)
meta = bundle["meta"] or {}
threshold = float((bundle["threshold"] or {}).get("threshold", 0.5))
model_label = (meta.get("model_label") or meta.get("model") or "xgboost").title()

hero(
    "Prediction Studio",
    f"Score any profile against the champion **{model_label}** model with SHAP-backed "
    "explanations — one customer at a time, or an entire CSV/Excel batch.",
    meta=f'<span class="cap-badge">threshold {fmt_percent(threshold, 1)}</span>',
)

tab_single, tab_batch = st.tabs(["Single profile", "Batch upload"])

# ===========================================================================
# SINGLE PROFILE
# ===========================================================================
with tab_single:
    form = st.form("predict_form", clear_on_submit=False)
    c_acct, c_plan, c_attrs = form.columns([5, 4, 5], gap="large")

    with c_acct:
        st.markdown("**ACCOUNT**")
        customer_id = form.text_input("Customer id", value=DEFAULT_INPUT["customer_id"])
        tenure = form.number_input("Tenure (months)", 0, 360, int(DEFAULT_INPUT["tenure"]), step=1)
        monthly = form.number_input("Monthly charges ($)", 0.0, 10000.0, float(DEFAULT_INPUT["monthly_charges"]), step=1.0)
        total = form.number_input("Total charges ($)", 0.0, 60000.0, float(DEFAULT_INPUT["total_charges"]), step=1.0)
        avg = form.number_input("Average monthly charge ($)", 0.0, 10000.0, float(DEFAULT_INPUT["avg_monthly_charge"]), step=1.0)
        services = form.number_input("Total services", 0, 12, int(DEFAULT_INPUT["total_services"]), step=1)

    with c_plan:
        st.markdown("**PLAN & BILLING**")
        internet = form.selectbox("Internet service", ["DSL", "Fiber optic", "No"], index=1)
        contract = form.selectbox("Contract", ["Month-to-month", "One year", "Two year"], index=0)
        payment = form.selectbox(
            "Payment method",
            ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
            index=0,
        )

    with c_attrs:
        st.markdown("**ACCOUNT ATTRIBUTES**")
        bools = {
            "gender_female": "Gender (female)",
            "senior_citizen": "Senior citizen",
            "paperless_billing": "Paperless billing",
            "partner": "Has partner",
            "dependents": "Has dependents",
            "multi_line": "Multiple lines",
            "online_security": "Online security",
            "online_backup": "Online backup",
            "device_protection": "Device protection",
            "tech_support": "Tech support",
            "streaming_tv": "Streaming TV",
            "streaming_movies": "Streaming movies",
        }
        cols = st.columns(2)
        toggles = {}
        for i, (key, label) in enumerate(bools.items()):
            with cols[i % 2]:
                toggles[key] = form.checkbox(label, value=bool(DEFAULT_INPUT[key]))

    submitted = form.form_submit_button("Predict churn", type="primary", width="stretch")

    def _build_row() -> dict:
        return {
            "customer_id": customer_id,
            "tenure": tenure,
            "monthly_charges": monthly,
            "total_charges": total,
            "avg_monthly_charge": avg,
            "total_services": services,
            "internet_service": internet,
            "contract": contract,
            "payment_method": payment,
            **toggles,
        }

    if submitted:
        with st.spinner("Scoring profile…"):
            engineered = rows_to_engineered([_build_row()])
            result = score_single(bundle["pipeline"], engineered)
            st.session_state["_last_prediction"] = {
                "engineered": engineered,
                "result": result,
            }

    if "_last_prediction" in st.session_state:
        last = st.session_state["_last_prediction"]
        result = last["result"]
        engineered = last["engineered"]
        prob = result["probability"]
        row = engineered.iloc[0]

        col_res, col_left = st.columns([2, 3], gap="large")
        with col_res:
            risk_gauge(prob)
            revenue_impact(prob, result["monthly_charges"], threshold)

        with col_left:
            st.markdown(
                f"""
                <div class="glass-panel">
                  <div style="font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:#9CA3AF">
                    Churn probability · {result["customer_id"]}</div>
                  <div style="font-size:2.6rem;font-weight:750;color:{'#EF4444' if prob >= 0.7 else '#F59E0B' if prob >= 0.5 else '#10B981'}">
                    {fmt_percent(prob, 1)}</div>
                  <div style="color:#9CA3AF;font-size:.78rem">conf {fmt_percent(prob, 0)} · {pretty(result['contract'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="insight-card">
                  <div class="cap">Verdict</div>
                  <p style="margin-top:.3rem">
                  {"This profile is flagged as <b style='color:#EF4444'>high risk</b> — intervene before the next billing cycle."
                   if prob >= 0.7 else
                   "This profile is <b style='color:#F59E0B'>medium risk</b> — monitor closely and consider proactive contact."
                   if prob >= 0.5 else
                   "This profile is <b style='color:#10B981'>low risk</b> — retention signals are strong."}
                  </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("Why — SHAP factors"):
            if st.button("Compute SHAP explanation", type="secondary"):
                from utils.explainability import local_explanation

                with st.spinner("Explaining…"):
                    expl = local_explanation(
                        bundle["classifier"], bundle["preprocessor"], row, prob, threshold
                    )
                st.session_state["_last_explanation"] = expl
            if "_last_explanation" in st.session_state:
                expl = st.session_state["_last_explanation"]
                c1, c2 = st.columns([3, 2], gap="large")
                with c1:
                    st.plotly_chart(charts.shap_waterfall(expl["contributions"]),
                                    width="stretch", config={"displayModeBar": False})
                with c2:
                    factor_list(expl["contributions"], limit=8)
                narrative_panel(expl["narrative"])

# ===========================================================================
# BATCH
# ===========================================================================
with tab_batch:
    st.markdown("**Batch scoring**")
    st.caption(
        "Upload a CSV or XLSX — either the raw Telco schema (customerID, SeniorCitizen, …) or the "
        "20-feature schema. Missing fields fall back to safe defaults; every row is validated before scoring."
    )
    upload = st.file_uploader("CSV or Excel file", type=["csv", "xlsx"], key="batch_upload")

    jsonl = st.text_area(
        "…or paste JSON records (one object per line)",
        height=110,
        placeholder='{"customer_id":"C-1001","tenure":3,"monthly_charges":89.0,"contract":"Month-to-month"}',
    )

    scored_batch = None
    if upload is not None:
        try:
            if upload.name.lower().endswith(".xlsx"):
                raw_df = pd.read_excel(upload)
            else:
                raw_df = pd.read_csv(upload)
            engineered = coerce_uploaded_to_engineered(raw_df)
            scored_batch = score_frame(bundle["pipeline"], engineered)
            st.success(f"Validated and scored {len(scored_batch)} rows.")
        except Exception as exc:  # pragma: no cover
            st.error(f"Could not parse the upload: {exc}")
    elif jsonl.strip():
        try:
            records = parse_jsonl(jsonl)
            engineered = rows_to_engineered(records)
            scored_batch = score_frame(bundle["pipeline"], engineered)
            st.success(f"Parsed {len(records)} record(s).")
        except Exception as exc:  # pragma: no cover
            st.error(f"Invalid JSON payload: {exc}")

    if scored_batch is not None and len(scored_batch) > 0:
        summary = batch_summary(scored_batch, threshold)
        metric_row(
            [
                {"label": "Rows scored", "value": fmt_number(summary["rows"]), "accent": "primary", "hint": "validated records"},
                {"label": "Expected churners", "value": fmt_number(summary["expected_churners"]), "accent": "danger", "hint": f"p ≥ {fmt_percent(threshold, 1)}"},
                {"label": "Mean risk", "value": fmt_percent(summary["mean_probability"], 1), "accent": "warning", "hint": "population mean"},
                {"label": "Annual exposure", "value": fmt_currency(summary["expected_annual_loss"]), "accent": "danger", "hint": "probability-weighted"},
            ]
        )

        st.markdown("**Risk distribution**")
        st.plotly_chart(
            charts.histogram(scored_batch["churn_probability"].to_numpy()),
            width="stretch",
            config={"displayModeBar": False},
        )

        view = scored_batch.sort_values("churn_probability", ascending=False)
        export_cols = ["customer_id", "tenure", "monthly_charges", "contract", "internet_service",
                       "payment_method", "churn_probability", "risk"]
        st.dataframe(
            view[export_cols].reset_index(drop=True),
            width="stretch",
            hide_index=True,
            height=360,
        )

        dl, rpt = st.columns([2, 2])
        with dl:
            st.download_button(
                "Download scored CSV",
                data=view.to_csv(index=False).encode("utf-8"),
                file_name="churn_batch_scored.csv",
                mime="text/csv",
            )
        with rpt:
            if st.button("Generate report", width="stretch"):
                path = report_generator.write_batch_report(view, summary)
                with open(path, "rb") as fh:
                    st.download_button(
                        "Download report (HTML)",
                        data=fh.read(),
                        file_name=path.name,
                        mime="text/html",
                    )
                st.success(f"Report saved to `reports/generated/{path.name}`")