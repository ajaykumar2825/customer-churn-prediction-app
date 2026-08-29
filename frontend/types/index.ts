/** TypeScript mirrors of the backend API contracts (backend/app/schemas). */

export type RiskLevel = "low" | "medium" | "high";
export type ContractType = "Month-to-month" | "One year" | "Two year";
export type InternetService = "DSL" | "Fiber optic" | "No";

/** Exactly the payload accepted by POST /api/v1/predict. */
export interface PredictionInput {
  customer_id: string;
  tenure: number;
  monthly_charges: number;
  total_charges: number;
  avg_monthly_charge: number;
  senior_citizen: boolean;
  gender_female: boolean;
  paperless_billing: boolean;
  partner: boolean;
  dependents: boolean;
  multi_line: boolean;
  online_security: boolean;
  online_backup: boolean;
  device_protection: boolean;
  tech_support: boolean;
  streaming_tv: boolean;
  streaming_movies: boolean;
  total_services: number;
  internet_service: string;
  contract: string;
  payment_method: string;
}

export interface FactorContribution {
  feature: string;
  value: number;
}

export interface Explanation {
  base_value: number | null;
  top_factors: FactorContribution[];
  contributions: FactorContribution[];
}

export interface PredictionResponse {
  customer_id: string;
  probability: number;
  risk_level: RiskLevel;
  predicted_churn: boolean;
  confidence: number;
  threshold: number;
  model: string;
  model_version: string;
  revenue_at_risk_monthly: number;
  retention_recommendation: string | null;
  top_factors: FactorContribution[];
  explanation: Explanation | null;
}

export interface BatchPredictionResponse {
  predictions: PredictionResponse[];
  summary: {
    count: number;
    mean_probability: number;
    high_risk: number;
    expected_churners: number;
    latency_ms_per_row: number;
  };
}

export interface CustomerOut {
  customer_id: string;
  tenure: number;
  monthly_charges: number;
  total_charges: number;
  avg_monthly_charge: number;
  contract: string;
  internet_service: string;
  payment_method: string;
  senior_citizen: boolean;
  gender_female: boolean;
  partner: boolean;
  dependents: boolean;
  paperless_billing: boolean;
  total_services: number;
  churn_probability: number;
  risk_level: RiskLevel;
  predicted_churn: boolean;
  observed_churn: boolean;
  created_at: string | null;
}

export interface CustomersPage {
  items: CustomerOut[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface TrendPoint {
  t: string;
  value: number;
}

export interface AnalyticsResponse {
  kpis: {
    total_customers: number;
    active_customers: number;
    churn_rate: number;
    revenue_at_risk: number;
    avg_satisfaction: number;
    avg_monthly_charges: number;
    high_risk_customers: number;
    retention_score: number;
  };
  trends: { revenue: TrendPoint[]; churn: TrendPoint[]; customers: TrendPoint[] };
  risk_distribution: { label: string; value: number }[];
  recent_predictions: Record<string, unknown>[];
  quick_stats: { rows: number; columns: number; churners: number };
}

export interface RevenueRisk {
  at_risk_customers: number;
  high_risk_customers: number;
  expected_monthly_loss: number;
  expected_annual_loss: number;
  total_monthly_revenue: number;
  percent_revenue_at_risk: number;
}

export interface RetentionRoi {
  customers_targeted: number;
  saved_customers: number;
  campaign_cost: number;
  retained_value_annual: number;
  roi: number;
}

export interface SegmentRow {
  segment: string;
  customers: number;
  churn_rate: number;
  monthly_charges_avg: number;
  expected_monthly_loss: number;
  predicted_churners: number;
}

export interface ContractImpact {
  current_avg_churn: number;
  hypothetical_avg_churn_after_contract: number;
  month_to_month_share: number;
  one_year_share: number;
  two_year_share: number;
  impact_note: string;
}

export interface RevenueBundle {
  revenue_at_risk: RevenueRisk;
  clv: number;
  retention_roi: RetentionRoi;
  segments: Record<string, SegmentRow[]>;
  contract_impact: ContractImpact;
}

/** GET /api/v1/metrics (model performance pack). */
export interface ModelMetrics {
  meta: Record<string, unknown>;
  leaderboard: Record<string, unknown>[];
  threshold: Record<string, unknown>;
  metrics: Record<string, unknown>;
  curves: Record<string, unknown>;
  confusion: Record<string, unknown>;
  importance: { shap: { importances: { feature: string; importance: number }[] }; permutation: unknown[] };
}

export interface ModelStatus {
  model: Record<string, unknown>;
  metrics: Record<string, unknown>;
  threshold: Record<string, unknown>;
  ready: boolean;
}

export interface CustomerExplain {
  customer_id: string;
  probability: number;
  risk_level: RiskLevel;
  explanation: Explanation;
}

export interface FeatureSpec {
  label: string;
  kind: "bool" | "int" | "number" | "enum";
  options?: string[];
  ge?: number;
  le?: number;
}

export type FeatureCatalogue = Record<string, FeatureSpec>;