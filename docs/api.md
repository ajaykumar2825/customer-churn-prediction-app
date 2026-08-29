# API reference — quick examples

Base URL (native): `http://localhost:8000`
Versioned prefix: `/api/v1`
Interactive docs: `http://localhost:8000/docs`

All request/response contracts are defined in `backend/app/schemas/` and mirrored by `frontend/types/index.ts`.

## Predict a single customer

```bash
curl -s http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "DEMO-0001",
    "tenure": 2,
    "monthly_charges": 89.9,
    "total_charges": 179.8,
    "internet_service": "Fiber optic",
    "contract": "Month-to-month",
    "payment_method": "Electronic check",
    "online_security": false,
    "tech_support": false
  }'
```

```json
{
  "customer_id": "DEMO-0001",
  "probability": 0.7432,
  "risk_level": "high",
  "predicted_churn": true,
  "confidence": 0.7432,
  "threshold": 0.335,
  "model": "xgboost",
  "model_version": "churn-xgb-2026-08-30-a3f21",
  "revenue_at_risk_monthly": 66.81,
  "retention_recommendation": "Immediate intervention: …",
  "top_factors": [ { "feature": "tenure", "value": 0.1214 }, "…" ],
  "explanation": { "base_value": 0.283, "top_factors": ["…"], "contributions": ["…"] }
}
```

> `avg_monthly_charge` is optional — it is derived as `total_charges / tenure`.

## Search and filter customers

```bash
curl -s "http://localhost:8000/api/v1/customers?search=7590&risk=low&sort_by=monthly_charges&page=1&page_size=10"
```

Returns `{ items, total, page, page_size, pages }`.

## Explain a stored customer

```bash
curl -s http://localhost:8000/api/v1/customers/7590-VHVEG/explain
```

Returns probability, risk_level and the full SHAP contribution list.

## Batch scoring (up to 10,000)

```bash
curl -s http://localhost:8000/api/v1/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"customers":[{"customer_id":"A","tenure":1,"monthly_charges":50,"total_charges":50}, "…"]}'
```

## Model registry

```bash
curl -s http://localhost:8000/api/v1/metrics            # leaderboard, curves, importance, meta
curl -s http://localhost:8000/api/v1/model/status       # champion health
curl -s http://localhost:8000/api/v1/feature-catalogue  # the 20-feature contract
```

## Observability

```bash
curl -s http://localhost:8000/health        # service liveness
curl -s http://localhost:8000/ready         # readiness (DB + model loaded)
curl -s http://localhost:8000/ops/metrics   # request counters/latency
```

## Error contract

| Status | Meaning |
| --- | --- |
| `400` | Validation failure (out-of-range values, unknown enum, blank fields) |
| `401` | Missing/invalid `X-API-Key` when `API_KEY` is configured |
| `404` | `{ "detail": "customer 'X' not found" }` |
| `429` | Rate limit exceeded |
| `503` | Model artifacts not loaded (`ModelNotReady`) |