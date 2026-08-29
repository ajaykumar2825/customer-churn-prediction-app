<div align="center">

# 🔮 Churn Intelligence

**Production-grade customer churn prediction platform** — gradient-boosted ML, SHAP-explainable decisions, executive business analytics.

Next.js 15 · FastAPI · XGBoost · SHAP · PostgreSQL · Redis · Docker · GitHub Actions

</div>

---

## Why this exists

Churn costs subscription businesses **an order of magnitude** more than acquisition. Churn Intelligence turns raw CRM data into a decision engine: predict **who** will churn, explain **why** the model believes it, and quantify **what it is worth** saving — all in one platform.

| Dimension | Capability |
| --- | --- |
| 🎯 **Predict** | Champion XGBoost model (test ROC-AUC **0.840**), tuned with Optuna over 8 candidate models |
| 🕵️ **Explain** | Per-customer SHAP contributions surfaced in the UI — no black boxes |
| 💰 **Monetize** | Revenue-at-risk, CLV, retention-campaign ROI and contract-migration plays |
| 🧩 **Operate** | Zero-infrastructure demo mode, Postgres/SQLite with seeded reference data, 77% backend test coverage |

## Architecture

```
frontend/     Next.js 15 dashboard (App Router, Tailwind, Recharts, shadcn-style UI kit)
backend/      FastAPI service — prediction, explanation, analytics, rate limiting, audit log
ml_pipeline/  Train → tune (Optuna) → evaluate → explain → business metrics → artifacts
database/     Postgres schema + reference-seed script
models/       Committed champion artifacts (clone-and-run, no training required)
data/         Telco churn dataset (7,032 clean records, 20 engineered features)
```

Client flow: `frontend` → `backend/api/v1` → model artifacts. When the API is unreachable the dashboard **gracefully renders realistic mock data** and flags demo mode.

## Quick start

### Prerequisites
- Python 3.10+ (**3.12 recommended** for production images; local dev verified on 3.14)
- Node 20 · npm 10
- Docker + Docker Compose (optional, for the full stack)

### Local development

```bash
# 1. Python environment + dependencies
python -m venv .venv
.\.venv\Scripts\activate          # Windows
source .venv/bin/activate         # macOS / Linux
pip install -r requirements.txt

# 2. Backend
cd backend
uvicorn app.main:app --reload     # http://localhost:8000/docs
# or: python -m pytest tests      # 22 tests

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev                       # http://localhost:3000
```

> No `DATABASE_URL` set? The API automatically uses the **in-memory demo store** — it re-scores the full dataset with the committed model at startup. Everything works with zero infrastructure.

### Retrain the model (optional)

```bash
python -m ml_pipeline.pipeline --tune-trials 25
```

Regenerates `models/*` artifacts and `reports/` — new champion is served automatically on backend restart.

### Full stack via Docker

```bash
cp .env.example .env              # then edit secrets
docker compose up --build
```

- Frontend → http://localhost:3000
- API + OpenAPI docs → http://localhost:8000/docs
- PostgreSQL → `localhost:5432` · Redis → `localhost:6379`

## The model

- **Champion:** XGBoost — test ROC-AUC **0.8404**, F1 **0.6349** @ probability threshold **0.335**
- **Contract of truth:** 20 engineered features (`backend/app/ml_feature_catalogue.py`), mirrored in the frontend types and prediction form
- **Explainability:** SHAP — global codes (the ggplot-equivalent importance) and local waterfall contributions per customer
- **Business metrics:** revenue-at-risk, probability-weighted MRR, CLV, campaign ROI, segment rollups

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/predict` | Score one profile, return SHAP factors + retention guidance |
| `POST` | `/api/v1/predict/batch` | Score up to 10,000 rows, summarize exposure |
| `POST` | `/api/v1/explain` | Local SHAP explanation for any profile |
| `GET` | `/api/v1/customers` | Search / filter / sort / paginate the base |
| `GET` | `/api/v1/customers/{id}/explain` | Why a stored customer is flagged |
| `GET` | `/api/v1/analytics` | Executive dashboard payload |
| `GET` | `/api/v1/revenue-risk` `· /segments` | Business strategy payloads |
| `GET` | `/api/v1/metrics` `· /feature-importance` `· /model/status` | Model registry |
| `GET` | `/health` `· /ready` `· /ops/metrics` | Observability |

## Reproducibility

- **Checks:** `ruff` clean, 22/22 backend tests, frontend `eslint` · `tsc --noEmit` · `next build` green.
- **GLP artifacts committed** (`models/` ≈ 1 MB) so the API and tests run without training.
- **CI:** `.github/workflows/ci.yml` (unit + lint + build) and `retrain.yml` (weekly scheduled / manual retraining).
- Deployment images pin **Python 3.12**; local dev verified on Python 3.14.

## Configuration

All knobs live in `backend/app/core/config.py` and `SettingsConfigDict` env mapping — copy `.env.example` → `.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | *(empty = demo mode)* | `postgresql+psycopg://…` or `sqlite:///…` |
| `REDIS_URL` | *(empty = in-memory)* | Cache/rate-limit backing store |
| `SECRET_KEY` | dev-only | **Override in production** |
| `DEFAULT_THRESHOLD` / `HIGH_RISK_THRESHOLD` | `0.5` / `0.7` | Risk bucketing + decision threshold |
| `SEED_ON_STARTUP` | `true` | Seed reference customers from the dataset |

## License

MIT — see [LICENSE](LICENSE).

> Built on the classic IBM Telco Customer Churn dataset. Original prototype by Ajay Kumar; rebuilt as a production platform in 2026.