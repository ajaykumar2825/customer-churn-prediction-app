# Architecture

This document describes the production topology, runtime behaviours and the data/feature contract of the Churn Intelligence platform.

## 1. System overview

```
                   ┌────────────────────────────────────────────┐
   Browser  ▸─────▶│  frontend/  Next.js 15 (App Router)        │
   :3000           │  Tailwind · Recharts · shadcn-style UI     │
                   └───────┬───────────────────────▲────────────┘
                           │ HTTP /api/v1/*        │ NEXT_PUBLIC_API_URL
                           ▼                       │
                   ┌──────────────────────────────┐│
   Health/diag        ┌── backbone ─────────────────┐
   :8000              │  backend/  FastAPI           │──┐
                      │  ModelService · CustomerSvc  │  │
                      │  rate-limit · audit · cache  │  │
                      └───────┬──────────┬───────────┘  │
                              │          │              │
              ┌───────────────▼──┐   ┌───▼──────────┐   ▼
              │ PostgreSQL/SQLite│   │ Redis (opt.) │  models/ (joblib)
              └──────────────────┘   └──────────────┘  SHAP artifacts
```

All services run as a single FastAPI process; the only external dependencies are optional (Postgres, Redis).

## 2. Service tiers

### 2.1 ML pipeline (`ml_pipeline/`)
- **Cleaning** (`features.py`): drops rows with blank `TotalCharges` (7,043 → 7,032), engineers the 20-feature contract.
- **Candidate registry** (`models.py`): 8 models — logistic regression, SGD, SVM, extra trees, random forest, gradient boosting, LightGBM, XGBoost, CatBoost.
- **Tuning** (`tune.py`): Optuna studies per model; tuned hyper-parameters merged into the factory defaults.
- **Evaluation** (`evaluate.py`): test-set metrics at the F1-maximising threshold, curves, confusion matrix, SHAP global importance + permutation importance.
- **Business layer** (`business.py`): revenue-at-risk, CLV, retention ROI, contract-impact simulation, segment rollups.
- **Artifacts** (`artifacts.py`): writes the `models/` + `reports/` contract consumed by the API.

### 2.2 Serving layer (`backend/app/`)
- `core/config.py` — all env knobs; `SettingsConfigDict` reads `.env` at repo root.
- `core/database.py` — SQLAlchemy engine; `database_online()` distinguishes Postgres/SQLite from demo mode.
- `core/cache.py`, `core/rate_limit.py` — Redis-backed with in-process LRU fallback.
- `services/model_service.py` — loads `models/*` once, idempotently; prediction, batch, local SHAP explain with **graceful fallback** to global-importance scaling when SHAP is unavailable.
- `services/demo_store.py` — lazy in-memory store; runs the pipeline over the full CSV at first use so the API is fully functional with zero infrastructure.
- `services/customer_service.py` — list/search/filter/paginate/export + dashboard aggregations, served from DB or demo store transparently.
- `services/seed_service.py` — seeds reference customers + audit log entries; called on startup when `SEED_ON_STARTUP=true`.

### 2.3 Frontend (`frontend/`)
- Pages are `"use client"` and fetch through `lib/api.ts`, which **falls back to realistic mock payloads** (`lib/mock-data.ts`) if the API is unreachable — the shell renders a "offline preview" banner via `fallbackNotice()`.
- Types in `types/index.ts` mirror the backend schemas verbatim (single source of truth for shapes).
- `lib/feature-catalogue.ts` mirrors `ml_feature_catalogue.py` so the prediction form renders exactly the accepted values.

## 3. Runtime behaviours

| Concern | Behaviour |
| --- | --- |
| Startup | DB online → create tables (SQLite) / rely on schema.sql (Postgres) + seed + load model. Model unavailable → `/predict` returns 503 `ModelNotReady`. |
| Demo mode | `DATABASE_URL` empty → all read paths serve from the in-memory store; predictions still use the real model. |
| Caching | `/analytics` cached 120s, `/revenue-risk` 300s (Redis or in-process). |
| Rate limiting | Fixed-window, 60 req / 60 s by default per client key. |
| Audit | Every prediction writes an `AuditLog` row (action, resource, detail, IP). |
| Export | `GET /customers/export` streams CSV of the current filtered view. |

## 4. The feature contract

Single source of truth: `backend/app/ml_feature_catalogue.py`.

- 13 binary: senior_citizen, gender_female, paperless_billing, partner, dependents, multi_line, online_security, online_backup, device_protection, tech_support, streaming_tv, streaming_movies.
- 4 numeric: tenure, monthly_charges, total_charges, avg_monthly_charge, total_services.
- 3 enums: internet_service (DSL / Fiber optic / No), contract (Month-to-month / One year / Two year), payment_method (Electronic check / Mailed check / Bank transfer (automatic) / Credit card (automatic)).

`avg_monthly_charge` is **auto-derived** (`total_charges / tenure`) by the Pydantic validator when not supplied. The frontend mirrors the contract in TS; CI fails if the two drift (tests + typecheck exercise both).

## 5. Security posture

- Secrets only via environment / `.env`; `SECRET_KEY` and `API_KEY` are **never committed**.
- CORS origin list configurable via `ALLOWED_ORIGINS` (production must not use `*`).
- Data validation at the edge (`pydantic` bounds on every numeric), rate limiting, request logging, audit trail.
- Docker images run non-privileged processes on pinned base images (`python:3.12-slim`, `node:20-alpine`, `postgres:16-alpine`).

## 6. Testing & CI

- Backend: `pytest` (22 tests, 77% coverage) + `ruff` — tests load the committed artifacts so they run without a training pass.
- Frontend: `eslint` (flat config), `tsc --noEmit`, `next build` (9 routes, static + one dynamic).
- CI (`.github/workflows/ci.yml`) runs all three in parallel; `retrain.yml` retrains on-request/weekly and uploads artifacts.

## 7. Python version note

Local development was verified on **Python 3.14** (dependency wheels resolved to minimum-pinned versions). Production images deliberately target **Python 3.12** for wheel availability of the full ML stack (catboost, xgboost, optuna, shap).