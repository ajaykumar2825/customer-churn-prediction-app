import type {
  AnalyticsResponse,
  CustomerExplain,
  CustomerOut,
  CustomersPage,
  ModelMetrics,
  ModelStatus,
  PredictionInput,
  PredictionResponse,
  RevenueBundle,
} from "@/types";

/** Credit-card style masking for customer ids in mock records. */
export function maskId(id: string): string {
  return id.length > 4 ? `•••• - ${id.slice(-4)}` : id;
}

const SHAP_IMPORTANCE = [
  { feature: "tenure", importance: 0.312 },
  { feature: "monthly_charges", importance: 0.187 },
  { feature: "contract_Month-to-month", importance: 0.154 },
  { feature: "internet_service_Fiber optic", importance: 0.121 },
  { feature: "payment_method_Electronic check", importance: 0.089 },
  { feature: "total_charges", importance: 0.061 },
  { feature: "tech_support_No", importance: 0.047 },
  { feature: "avg_monthly_charge", importance: 0.029 },
  { feature: "paperless_billing", importance: 0.018 },
  { feature: "online_security_No", importance: 0.011 },
];

const PERMUTATION = [
  { feature: "tenure", importance: 0.221 },
  { feature: "monthly_charges", importance: 0.143 },
  { feature: "contract_Month-to-month", importance: 0.11 },
  { feature: "internet_service_Fiber optic", importance: 0.082 },
  { feature: "total_charges", importance: 0.054 },
];

export const MOCK_CUSTOMERS: CustomerOut[] = [
  { customer_id: "7590-VHVEG", tenure: 29, monthly_charges: 53.85, total_charges: 1562.25, avg_monthly_charge: 53.87, contract: "One year", internet_service: "DSL", payment_method: "Electronic check", senior_citizen: false, gender_female: false, partner: false, dependents: false, paperless_billing: true, total_services: 1, churn_probability: 0.2147, risk_level: "low", predicted_churn: false, observed_churn: false, created_at: "2026-01-12T09:40:00" },
  { customer_id: "5575-GNVDE", tenure: 61, monthly_charges: 108.35, total_charges: 6608.7, avg_monthly_charge: 108.34, contract: "Two year", internet_service: "Fiber optic", payment_method: "Credit card (automatic)", senior_citizen: false, gender_female: true, partner: true, dependents: false, paperless_billing: true, total_services: 8, churn_probability: 0.0892, risk_level: "low", predicted_churn: false, observed_churn: false, created_at: "2026-02-03T14:12:00" },
  { customer_id: "3668-QPYBK", tenure: 2, monthly_charges: 19.85, total_charges: 39.7, avg_monthly_charge: 19.85, contract: "Month-to-month", internet_service: "DSL", payment_method: "Mailed check", senior_citizen: false, gender_female: true, partner: false, dependents: false, paperless_billing: true, total_services: 0, churn_probability: 0.7184, risk_level: "high", predicted_churn: true, observed_churn: true, created_at: "2026-03-18T08:22:00" },
  { customer_id: "7795-CFOCW", tenure: 45, monthly_charges: 84.5, total_charges: 3802.5, avg_monthly_charge: 84.5, contract: "One year", internet_service: "Fiber optic", payment_method: "Bank transfer (automatic)", senior_citizen: false, gender_female: true, partner: true, dependents: true, paperless_billing: false, total_services: 7, churn_probability: 0.1288, risk_level: "low", predicted_churn: false, observed_churn: false, created_at: "2026-01-22T11:05:00" },
  { customer_id: "9237-HQITU", tenure: 41, monthly_charges: 99.65, total_charges: 4085.65, avg_monthly_charge: 99.65, contract: "Month-to-month", internet_service: "Fiber optic", payment_method: "Electronic check", senior_citizen: false, gender_female: true, partner: false, dependents: false, paperless_billing: true, total_services: 4, churn_probability: 0.5841, risk_level: "medium", predicted_churn: true, observed_churn: false, created_at: "2026-04-01T16:44:00" },
  { customer_id: "9305-CDSKC", tenure: 12, monthly_charges: 55.2, total_charges: 662.4, avg_monthly_charge: 55.2, contract: "Month-to-month", internet_service: "DSL", payment_method: "Mailed check", senior_citizen: true, gender_female: false, partner: false, dependents: false, paperless_billing: true, total_services: 1, churn_probability: 0.6929, risk_level: "high", predicted_churn: true, observed_churn: false, created_at: "2026-02-14T10:30:00" },
  { customer_id: "6739-OKKMS", tenure: 3, monthly_charges: 71.1, total_charges: 213.3, avg_monthly_charge: 71.1, contract: "Month-to-month", internet_service: "Fiber optic", payment_method: "Electronic check", senior_citizen: false, gender_female: false, partner: false, dependents: false, paperless_billing: false, total_services: 3, churn_probability: 0.7631, risk_level: "high", predicted_churn: true, observed_churn: false, created_at: "2026-03-30T09:18:00" },
  { customer_id: "1782-OKRQC", tenure: 71, monthly_charges: 106.7, total_charges: 7575.7, avg_monthly_charge: 106.7, contract: "Two year", internet_service: "Fiber optic", payment_method: "Credit card (automatic)", senior_citizen: false, gender_female: false, partner: true, dependents: true, paperless_billing: true, total_services: 8, churn_probability: 0.0621, risk_level: "low", predicted_churn: false, observed_churn: false, created_at: "2026-01-05T15:02:00" },
];

export const MOCK_PAGE: CustomersPage = {
  items: MOCK_CUSTOMERS,
  total: 7032,
  page: 1,
  page_size: 8,
  pages: 879,
};

export const MOCK_ANALYTICS: AnalyticsResponse = {
  kpis: {
    total_customers: 7032,
    active_customers: 5170,
    churn_rate: 0.2648,
    revenue_at_risk: 49280.62,
    avg_satisfaction: 3.44,
    avg_monthly_charges: 64.76,
    high_risk_customers: 1863,
    retention_score: 0.7352,
  },
  trends: {
    revenue: [
      { t: "<1m", value: 94120.4 },
      { t: "1-6m", value: 141803.6 },
      { t: "6-12m", value: 119845.9 },
      { t: "1-2y", value: 92410.2 },
      { t: "2-4y", value: 61037.8 },
      { t: "4y+", value: 31204.5 },
    ],
    churn: [
      { t: "<1m", value: 482 },
      { t: "1-6m", value: 714 },
      { t: "6-12m", value: 596 },
      { t: "1-2y", value: 342 },
      { t: "2-4y", value: 188 },
      { t: "4y+", value: 79 },
    ],
    customers: [
      { t: "2026-03-01", value: 6332 },
      { t: "2026-03-02", value: 6385 },
      { t: "2026-03-03", value: 6411 },
      { t: "2026-03-04", value: 6470 },
      { t: "2026-03-05", value: 6509 },
      { t: "2026-03-06", value: 6552 },
      { t: "2026-03-07", value: 6598 },
      { t: "2026-03-08", value: 6651 },
      { t: "2026-03-09", value: 6707 },
      { t: "2026-03-10", value: 6762 },
      { t: "2026-03-11", value: 6819 },
      { t: "2026-03-12", value: 6858 },
      { t: "2026-03-13", value: 6904 },
      { t: "2026-03-14", value: 6966 },
      { t: "2026-03-15", value: 7032 },
    ],
  },
  risk_distribution: [
    { label: "Low Risk", value: 3958 },
    { label: "Medium Risk", value: 1211 },
    { label: "High Risk", value: 1863 },
  ],
  recent_predictions: MOCK_CUSTOMERS.slice(0, 4).map((c) => ({
    customer_id: c.customer_id,
    churn_probability: c.churn_probability,
    probability: c.churn_probability,
    contract: c.contract,
    monthly_charges: c.monthly_charges,
    payment_method: c.payment_method,
  })),
  quick_stats: { rows: 7032, columns: 21, churners: 1862 },
};

export const MOCK_BUNDLE: RevenueBundle = {
  revenue_at_risk: {
    at_risk_customers: 2063,
    high_risk_customers: 917,
    expected_monthly_loss: 128640.45,
    expected_annual_loss: 1543685.4,
    total_monthly_revenue: 455394.72,
    percent_revenue_at_risk: 28.2,
  },
  clv: 1123.4,
  retention_roi: {
    customers_targeted: 1582,
    saved_customers: 553.7,
    campaign_cost: 55370.0,
    retained_value_annual: 472894.0,
    roi: 7.54,
  },
  segments: {
    contract: [
      { segment: "Month-to-month", customers: 3875, churn_rate: 41.2, monthly_charges_avg: 61.22, expected_monthly_loss: 99478.6, predicted_churners: 1596 },
      { segment: "One year", customers: 1741, churn_rate: 11.4, monthly_charges_avg: 66.93, expected_monthly_loss: 13204.9, predicted_churners: 199 },
      { segment: "Two year", customers: 1416, churn_rate: 4.6, monthly_charges_avg: 73.19, expected_monthly_loss: 4740.1, predicted_churners: 65 },
    ],
    payment_method: [
      { segment: "Electronic check", customers: 2366, churn_rate: 45.1, monthly_charges_avg: 62.88, expected_monthly_loss: 67276.4, predicted_churners: 1067 },
      { segment: "Mailed check", customers: 1757, churn_rate: 24.6, monthly_charges_avg: 60.36, expected_monthly_loss: 26425.1, predicted_churners: 432 },
      { segment: "Bank transfer (automatic)", customers: 1429, churn_rate: 15.2, monthly_charges_avg: 67.44, expected_monthly_loss: 14606.8, predicted_churners: 217 },
      { segment: "Credit card (automatic)", customers: 1480, churn_rate: 12.8, monthly_charges_avg: 69.01, expected_monthly_loss: 12928.2, predicted_churners: 189 },
    ],
    internet_service: [
      { segment: "Fiber optic", customers: 3503, churn_rate: 41.9, monthly_charges_avg: 89.14, expected_monthly_loss: 132491.5, predicted_churners: 1468 },
      { segment: "DSL", customers: 2604, churn_rate: 15.3, monthly_charges_avg: 44.85, expected_monthly_loss: 18650.3, predicted_churners: 398 },
      { segment: "No", customers: 925, churn_rate: 5.6, monthly_charges_avg: 24.11, expected_monthly_loss: 2299.1, predicted_churners: 52 },
    ],
    tenure_group: [
      { segment: "<1m", customers: 1215, churn_rate: 52.1, monthly_charges_avg: 49.62, expected_monthly_loss: 32514.6, predicted_churners: 633 },
      { segment: "1-6m", customers: 1474, churn_rate: 38.4, monthly_charges_avg: 61.83, expected_monthly_loss: 35010.4, predicted_churners: 566 },
      { segment: "6-12m", customers: 1283, churn_rate: 27.6, monthly_charges_avg: 65.3, expected_monthly_loss: 23119.7, predicted_churners: 354 },
      { segment: "1-2y", customers: 1196, churn_rate: 17.9, monthly_charges_avg: 70.12, expected_monthly_loss: 15008.3, predicted_churners: 214 },
      { segment: "2-4y", customers: 1122, churn_rate: 8.6, monthly_charges_avg: 73.9, expected_monthly_loss: 8125.1, predicted_churners: 96 },
      { segment: "4y+", customers: 742, churn_rate: 3.9, monthly_charges_avg: 75.6, expected_monthly_loss: 2127.9, predicted_churners: 29 },
    ],
  },
  contract_impact: {
    current_avg_churn: 26.5,
    hypothetical_avg_churn_after_contract: 22.5,
    month_to_month_share: 55.1,
    one_year_share: 24.8,
    two_year_share: 20.1,
    impact_note:
      "Migrating month-to-month customers to one-year contracts historically reduces average churn probability by roughly 4 percentage points.",
  },
};

export const MOCK_METRICS: ModelMetrics = {
  meta: {
    model: "xgboost",
    run_id: "churn-xgb-2026-08-30-a3f21",
    trained_at: "2026-08-30T03:12:44",
    dataset: "telco_churn.csv",
    rows: 7032,
    tune_trials: 25,
    test_size: 0.2,
    seed: 42,
  },
  leaderboard: [
    { model: "xgboost", test_roc_auc: 0.8404, test_f1: 0.6349, test_precision: 0.5774, test_recall: 0.7052, avg_fit_seconds: 1.24, tuning: "tuned" },
    { model: "lightgbm", test_roc_auc: 0.8387, test_f1: 0.629, test_precision: 0.571, test_recall: 0.7, avg_fit_seconds: 0.62, tuning: "tuned" },
    { model: "gradient_boosting", test_roc_auc: 0.8331, test_f1: 0.6192, test_precision: 0.565, test_recall: 0.685, avg_fit_seconds: 2.1, tuning: "default" },
    { model: "catboost", test_roc_auc: 0.8299, test_f1: 0.6221, test_precision: 0.563, test_recall: 0.695, avg_fit_seconds: 4.8, tuning: "default" },
    { model: "random_forest", test_roc_auc: 0.8268, test_f1: 0.6082, test_precision: 0.56, test_recall: 0.665, avg_fit_seconds: 1.9, tuning: "default" },
    { model: "logistic_regression", test_roc_auc: 0.8295, test_f1: 0.5884, test_precision: 0.552, test_recall: 0.63, avg_fit_seconds: 0.2, tuning: "default" },
    { model: "svm", test_roc_auc: 0.823, test_f1: 0.618, test_precision: 0.555, test_recall: 0.696, avg_fit_seconds: 8.4, tuning: "default" },
    { model: "extra_trees", test_roc_auc: 0.818, test_f1: 0.5972, test_precision: 0.545, test_recall: 0.66, avg_fit_seconds: 1.1, tuning: "default" },
  ],
  threshold: { threshold: 0.335, optimized: true, note: "F1-maximizing decision threshold on held-out validation" },
  metrics: {
    accuracy: 0.8047,
    precision: 0.5774,
    recall: 0.7052,
    f1: 0.6349,
    roc_auc: 0.8404,
    average_precision: 0.7091,
    threshold: 0.335,
  },
  curves: {
    roc: { fpr: [0, 0.021, 0.053, 0.112, 0.197, 0.318, 0.472, 0.634, 0.812, 0.943, 1], tpr: [0, 0.248, 0.397, 0.553, 0.672, 0.769, 0.842, 0.905, 0.961, 0.991, 1] },
    pr: { precision: [0.265, 0.462, 0.571, 0.634, 0.688, 0.71, 0.748, 0.79, 0.871, 1, 1], recall: [1, 0.93, 0.851, 0.774, 0.69, 0.61, 0.47, 0.331, 0.202, 0.087, 0] },
  },
  confusion: {
    tn: 1009, fp: 116, fn: 133, tp: 316,
    accuracy: 0.8047,
    note: "Test-set confusion at threshold 0.335",
  },
  importance: { shap: { importances: SHAP_IMPORTANCE }, permutation: PERMUTATION },
};

export const MOCK_MODEL_STATUS: ModelStatus = {
  model: MOCK_METRICS.meta,
  metrics: MOCK_METRICS.metrics,
  threshold: MOCK_METRICS.threshold,
  ready: true,
};

const factor = (feature: string, value: number) => ({ feature, value });

export const MOCK_PREDICTION_LOW: PredictionResponse = {
  customer_id: "7590-VHVEG",
  probability: 0.2147,
  risk_level: "low",
  predicted_churn: false,
  confidence: 0.7853,
  threshold: 0.335,
  model: "xgboost",
  model_version: "churn-xgb-2026-08-30-a3f21",
  revenue_at_risk_monthly: 11.56,
  retention_recommendation: null,
  top_factors: [
    factor("tenure", -0.0841),
    factor("contract_Two year", -0.0492),
    factor("online_security_Yes", -0.0318),
    factor("monthly_charges", 0.0187),
    factor("avg_monthly_charge", -0.0143),
  ],
  explanation: {
    base_value: 0.283,
    top_factors: [
      factor("tenure", -0.0841),
      factor("contract_Two year", -0.0492),
      factor("online_security_Yes", -0.0318),
      factor("monthly_charges", 0.0187),
      factor("avg_monthly_charge", -0.0143),
    ],
    contributions: [
      factor("tenure", -0.0841),
      factor("contract_Two year", -0.0492),
      factor("online_security_Yes", -0.0318),
      factor("monthly_charges", 0.0187),
      factor("avg_monthly_charge", -0.0143),
      factor("payment_method_Credit card (automatic)", -0.0089),
      factor("tech_support_Yes", -0.0062),
      factor("gender_female", -0.0023),
      factor("paperless_billing", 0.0044),
      factor("partner_Yes", -0.0031),
    ],
  },
};

export const MOCK_PREDICTION_HIGH: PredictionResponse = {
  customer_id: "3668-QPYBK",
  probability: 0.7184,
  risk_level: "high",
  predicted_churn: true,
  confidence: 0.7184,
  threshold: 0.335,
  model: "xgboost",
  model_version: "churn-xgb-2026-08-30-a3f21",
  revenue_at_risk_monthly: 14.26,
  retention_recommendation:
    "Immediate intervention: offer one-year contract with month-of-free service, waive early-exit fees, and unlock senior retention agent.",
  top_factors: [
    factor("tenure", 0.1214),
    factor("contract_Month-to-month", 0.0923),
    factor("internet_service_Fiber optic", 0.0618),
    factor("tech_support_No", 0.0441),
    factor("payment_method_Electronic check", 0.0337),
  ],
  explanation: {
    base_value: 0.283,
    top_factors: [
      factor("tenure", 0.1214),
      factor("contract_Month-to-month", 0.0923),
      factor("internet_service_Fiber optic", 0.0618),
      factor("tech_support_No", 0.0441),
      factor("payment_method_Electronic check", 0.0337),
    ],
    contributions: [
      factor("tenure", 0.1214),
      factor("contract_Month-to-month", 0.0923),
      factor("internet_service_Fiber optic", 0.0618),
      factor("tech_support_No", 0.0441),
      factor("payment_method_Electronic check", 0.0337),
      factor("total_charges", 0.0282),
      factor("avg_monthly_charge", 0.0194),
      factor("online_security_No", 0.0168),
      factor("paperless_billing", 0.0102),
      factor("dependents_No", 0.0085),
    ],
  },
};

export const MOCK_EXPLAIN_HIGH: CustomerExplain = {
  customer_id: "3668-QPYBK",
  probability: 0.7184,
  risk_level: "high",
  explanation: MOCK_PREDICTION_HIGH.explanation!,
};

export const MOCK_EXPLAIN_LOW: CustomerExplain = {
  customer_id: "7590-VHVEG",
  probability: 0.2147,
  risk_level: "low",
  explanation: MOCK_PREDICTION_LOW.explanation!,
};

export const MOCK_CUSTOMER_DETAIL = (id: string): CustomerOut | null =>
  MOCK_CUSTOMERS.find((c) => c.customer_id === id) ?? null;

export const DEFAULT_INPUT: PredictionInput = {
  customer_id: "DEMO-0001",
  tenure: 24,
  monthly_charges: 79.99,
  total_charges: 1919.76,
  avg_monthly_charge: 79.99,
  senior_citizen: false,
  gender_female: true,
  paperless_billing: true,
  partner: false,
  dependents: false,
  multi_line: true,
  online_security: false,
  online_backup: false,
  device_protection: true,
  tech_support: false,
  streaming_tv: true,
  streaming_movies: false,
  total_services: 5,
  internet_service: "Fiber optic",
  contract: "Month-to-month",
  payment_method: "Electronic check",
};