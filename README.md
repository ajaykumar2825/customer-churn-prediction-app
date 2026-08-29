# Churn Intelligence — Customer Churn Prediction Platform

An end-to-end churn prediction platform shipped as a **single Streamlit application**.
It trains, evaluates and explains a gradient-boosted champion model over the Telco
Customer Churn dataset, then turns predictions into retention economics.

```
pip install -r requirements.txt
streamlit run main.py
```

Runs on **Python 3.12+** (developed on 3.14). No Node, Docker or database required.

---

## What's inside

| Page | Purpose |
| --- | --- |
| **Overview** | Live health of the whole book — churn rate, at-risk revenue, contract mix, tenure cohorts |
| **Customer Analytics** | 11 sidebar filters slice the base; segment tables and distribution views per filter |
| **Predict Churn** | Single-customer form, batch upload (CSV / XLSX / JSONL), downloadable scoring + HTML report |
| **Model Performance** | Held-out metrics, threshold optimisation, calibration, lift/gain, confusion matrix, leaderboard, learning curve |
| **SHAP Explainability** | Global SHAP summary + per-customer waterfall with plain-English narratives |
| **Retention Strategy** | Revenue at risk, CLV, campaign ROI, contract-migration play, cohort heatmap |
| **About Project** | Model card, methodology, feature catalogue, author block |

## Architecture

```
main.py                  one Streamlit entrypoint (st.navigation over 7 pages)
├── pages/               the 7 product pages
├── components/          layout, sidebar filters, metric cards, charts, tables, prediction card
├── utils/               loaders, preprocessing, prediction, explainability, formatting, stats, reports
├── ml_pipeline/         training + evaluation + SHAP + business analytics (standalone, reusable)
├── models/              persisted artifacts (joblib pipelines + JSON metrics + SHAP plots)
├── data/                data/telco_churn.csv (committed)
├── reports/             generated HTML report snapshots (gitignored)
├── scripts/             scripts/smoke_test.py — headless page runner (Streamlit AppTest)
└── .streamlit/          config.toml theme + secrets.toml.example
```

### Model

- **20 engineered features** derived from 21 raw columns (contract windows, add-on counts,
  average spend, billing behaviour).
- Champion **XGBoost** picked from 7 candidates tuned with **Optuna**; evaluated on a
  stratified 20% hold-out.
- Held-out results: ROC-AUC **0.8404**, PR-AUC **0.6511**, F1 **0.6349** at an
  optimised threshold of **0.335**.
- SHAP explains every prediction; `reports/generated/` holds shareable batch HTML reports.

### Reproducing the training job

Artifacts are committed, so the app boots instantly from `models/`. To retrain and
re-persist everything (including the analysed SHAP plots):

```
python -m ml_pipeline.pipeline            # quick run (no Optuna tuning)
python -m ml_pipeline.pipeline --tune-trials 40
```

Missing artefacts trigger an automatic training fallback on first run.

## Deployment

**Streamlit Community Cloud** — point it at the repo and set `main.py` as the entrypoint.
The app is fully deterministic (seeded), self-contained and uses zero external services.

Optional author details live in `.streamlit/secrets.toml` (copy from
`secrets.toml.example`):

```toml
[app]
owner = "Your name"
company = "Your company"
email = "you@example.com"
github = "https://github.com/you"
linkedin = "https://www.linkedin.com/in/you"
```

## Development

```bash
python -m compileall -q main.py ml_pipeline components utils pages scripts
python scripts/smoke_test.py        # renders every page headless via AppTest
```

CI (`.github/workflows/ci.yml`) byte-compiles the sources, runs the AppTest smoke
suite and re-runs the pipeline as a smoke job. A manual `retrain` workflow retrains
the champion with Optuna and uploads artifacts.

## Data & licensing

Dataset: IBM/Kaggle `telco-customer-churn` (7,043 rows → 7,032 after cleaning).
Code: MIT — see `LICENSE`.