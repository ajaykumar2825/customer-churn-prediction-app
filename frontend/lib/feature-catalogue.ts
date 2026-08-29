import type { FeatureSpec } from "@/types";

/**
 * Feature contract mirrored from backend/app/ml_feature_catalogue.py
 * so the prediction form renders the exact accepted values.
 */
export const FEATURE_CATALOGUE: Record<string, FeatureSpec> = {
  tenure: { label: "Tenure (months)", kind: "int", ge: 0, le: 360 },
  monthly_charges: { label: "Monthly charges ($)", kind: "number", ge: 0 },
  total_charges: { label: "Total charges ($)", kind: "number", ge: 0 },
  avg_monthly_charge: { label: "Average monthly charge ($)", kind: "number", ge: 0 },
  senior_citizen: { label: "Senior citizen", kind: "bool" },
  gender_female: { label: "Gender (female)", kind: "bool" },
  paperless_billing: { label: "Paperless billing", kind: "bool" },
  partner: { label: "Has partner", kind: "bool" },
  dependents: { label: "Has dependents", kind: "bool" },
  multi_line: { label: "Multiple lines", kind: "bool" },
  online_security: { label: "Online security", kind: "bool" },
  online_backup: { label: "Online backup", kind: "bool" },
  device_protection: { label: "Device protection", kind: "bool" },
  tech_support: { label: "Tech support", kind: "bool" },
  streaming_tv: { label: "Streaming TV", kind: "bool" },
  streaming_movies: { label: "Streaming movies", kind: "bool" },
  total_services: { label: "Total services", kind: "int", ge: 0, le: 12 },
  internet_service: { label: "Internet service", kind: "enum", options: ["DSL", "Fiber optic", "No"] },
  contract: { label: "Contract", kind: "enum", options: ["Month-to-month", "One year", "Two year"] },
  payment_method: {
    label: "Payment method",
    kind: "enum",
    options: ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
  },
};

export const BOOL_FEATURES = Object.entries(FEATURE_CATALOGUE)
  .filter(([, spec]) => spec.kind === "bool")
  .map(([key]) => key);

export const NUMERIC_FEATURES = Object.entries(FEATURE_CATALOGUE)
  .filter(([, spec]) => spec.kind === "int" || spec.kind === "number")
  .map(([key]) => key);

export const ENUM_FEATURES = Object.entries(FEATURE_CATALOGUE)
  .filter(([, spec]) => spec.kind === "enum")
  .map(([key]) => key);