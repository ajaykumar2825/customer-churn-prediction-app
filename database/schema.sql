-- Churn Intelligence Platform — PostgreSQL schema
-- Mirrors backend/app/models/orm.py (SQLAlchemy). For local development the
-- API can fall back to SQLite; this schema is the production target.

CREATE TABLE IF NOT EXISTS customers (
    id                    SERIAL PRIMARY KEY,
    customer_id           VARCHAR(32)  NOT NULL UNIQUE,
    senior_citizen        BOOLEAN      NOT NULL DEFAULT FALSE,
    gender_female         BOOLEAN      NOT NULL DEFAULT FALSE,
    partner               BOOLEAN      NOT NULL DEFAULT FALSE,
    dependents            BOOLEAN      NOT NULL DEFAULT FALSE,
    tenure                INTEGER      NOT NULL DEFAULT 0,
    monthly_charges       DOUBLE PRECISION NOT NULL DEFAULT 0,
    total_charges         DOUBLE PRECISION NOT NULL DEFAULT 0,
    avg_monthly_charge    DOUBLE PRECISION NOT NULL DEFAULT 0,
    paperless_billing     BOOLEAN      NOT NULL DEFAULT FALSE,
    multi_line            BOOLEAN      NOT NULL DEFAULT FALSE,
    online_security       BOOLEAN      NOT NULL DEFAULT FALSE,
    online_backup         BOOLEAN      NOT NULL DEFAULT FALSE,
    device_protection     BOOLEAN      NOT NULL DEFAULT FALSE,
    tech_support          BOOLEAN      NOT NULL DEFAULT FALSE,
    streaming_tv          BOOLEAN      NOT NULL DEFAULT FALSE,
    streaming_movies      BOOLEAN      NOT NULL DEFAULT FALSE,
    total_services        INTEGER      NOT NULL DEFAULT 0,
    internet_service      VARCHAR(16)  NOT NULL DEFAULT 'No',
    contract              VARCHAR(32)  NOT NULL DEFAULT 'Month-to-month',
    payment_method        VARCHAR(64)  NOT NULL DEFAULT 'Electronic check',
    churn_probability     DOUBLE PRECISION NOT NULL DEFAULT 0,
    risk_level            VARCHAR(16)  NOT NULL DEFAULT 'low',
    predicted_churn       BOOLEAN      NOT NULL DEFAULT FALSE,
    observed_churn        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_customers_risk      ON customers (risk_level);
CREATE INDEX IF NOT EXISTS idx_customers_contract  ON customers (contract);
CREATE INDEX IF NOT EXISTS idx_customers_prob      ON customers (churn_probability DESC);

CREATE TABLE IF NOT EXISTS predictions (
    id              SERIAL PRIMARY KEY,
    customer_id     VARCHAR(32)  NOT NULL,
    probability     DOUBLE PRECISION NOT NULL DEFAULT 0,
    risk_level      VARCHAR(16)  NOT NULL DEFAULT 'low',
    predicted_churn BOOLEAN      NOT NULL DEFAULT FALSE,
    model_version   VARCHAR(32)  NOT NULL DEFAULT 'default',
    payload         TEXT         NOT NULL DEFAULT '{}',
    explanation     TEXT         NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_predictions_customer ON predictions (customer_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created  ON predictions (created_at DESC);

CREATE TABLE IF NOT EXISTS users (
    id           SERIAL PRIMARY KEY,
    email        VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(120) NOT NULL DEFAULT '',
    role         VARCHAR(32)  NOT NULL DEFAULT 'analyst',
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id         SERIAL PRIMARY KEY,
    actor      VARCHAR(120) NOT NULL DEFAULT 'anonymous',
    action     VARCHAR(64)  NOT NULL,
    resource   VARCHAR(120) NOT NULL DEFAULT '',
    detail     TEXT         NOT NULL DEFAULT '',
    ip         VARCHAR(64)  NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs (created_at DESC);