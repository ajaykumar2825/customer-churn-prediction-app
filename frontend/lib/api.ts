import type {
  AnalyticsResponse,
  CustomerExplain,
  CustomerOut,
  CustomersPage,
  FeatureCatalogue,
  ModelMetrics,
  ModelStatus,
  PredictionInput,
  PredictionResponse,
  RevenueBundle,
} from "@/types";
import {
  DEFAULT_INPUT,
  MOCK_ANALYTICS,
  MOCK_BUNDLE,
  MOCK_CUSTOMER_DETAIL,
  MOCK_EXPLAIN_HIGH,
  MOCK_EXPLAIN_LOW,
  MOCK_METRICS,
  MOCK_MODEL_STATUS,
  MOCK_PAGE,
  MOCK_PREDICTION_HIGH,
  MOCK_PREDICTION_LOW,
} from "@/lib/mock-data";
import { FEATURE_CATALOGUE } from "@/lib/feature-catalogue";

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const API_BASE = `${API_URL}/api/v1`;

/** Track whether the client has silently failed over to mock mode. */
let _fallbackActive = false;
export const isFallbackActive = () => _fallbackActive;

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

let suppressErrorLog = false;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body).slice(0, 240);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") ?? "";
  return (ct.includes("json") ? await res.json() : ((await res.text()) as unknown as T)) as T;
}

/** Attempt a real API call, falling back to the mock payload on transport errors. */
async function withFallback<T>(call: () => Promise<T>, mocked: () => T, notify = true): Promise<T> {
  if (suppressErrorLog) return mocked();
  try {
    return await call();
  } catch (err) {
    _fallbackActive = true;
    if (notify) {
      summary(`API unavailable at ${API_URL} — showing offline preview.`, err);
    }
    return mocked();
  }
}

interface FallbackNotice {
  message: string;
  preview: boolean;
  apiUrl: string;
}

/** Latest fallback notice, rendered as a demo-mode banner by the shell. */
export const fallbackNotice: () => FallbackNotice | null = () =>
  _fallbackActive ? { message: "Live API unreachable — dashboard is running on realistic mock data.", preview: true, apiUrl: API_URL } : null;

function summary(_msg: string, _ctx?: unknown) {
  // Logged exactly once; repeated failures are silent to avoid console spam.
  suppressErrorLog = true;
  console.warn(`[churn-ui] API unreachable at ${API_URL}. Falling back to offline preview data.`);
}

const qs = (params: Record<string, string | number | boolean | null | undefined>) => {
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") search.set(k, String(v));
  }
  const s = search.toString();
  return s ? `?${s}` : "";
};

export const api = {
  baseUrl: API_BASE,
  fallbackActive: () => isFallbackActive(),

  // ------------------------------------------------------------- analytics
  async getAnalytics(): Promise<AnalyticsResponse> {
    return withFallback(() => request<AnalyticsResponse>("/analytics"), () => MOCK_ANALYTICS);
  },

  async getRevenueBundle(): Promise<RevenueBundle> {
    return withFallback(
      async () => {
        const { bundle } = await request<{ bundle: RevenueBundle }>("/revenue-risk");
        return bundle;
      },
      () => MOCK_BUNDLE,
    );
  },

  async getSegments(): Promise<RevenueBundle["segments"]> {
    return withFallback(
      async () => (await request<{ segments: RevenueBundle["segments"] }>("/segments")).segments,
      () => MOCK_BUNDLE.segments,
    );
  },

  // --------------------------------------------------------------- customers
  async getCustomers(params: {
    search?: string;
    contract?: string;
    risk?: string;
    churn?: boolean;
    sort_by?: string;
    ascending?: boolean;
    page?: number;
    page_size?: number;
  } = {}): Promise<CustomersPage> {
    return withFallback(
      () =>
        request<CustomersPage>(
          `/customers${qs({ ...params, ascending: params.ascending ? "true" : "false" })}`,
        ),
      () => {
        const { search, risk, page = 1, page_size = 8 } = params;
        let items = [...MOCK_PAGE.items];
        if (search) items = items.filter((c) => c.customer_id.toLowerCase().includes(search.toLowerCase()));
        if (risk) items = items.filter((c) => c.risk_level === risk);
        return { ...MOCK_PAGE, items, total: items.length, pages: Math.max(Math.ceil(items.length / page_size), 1), page };
      },
      false,
    );
  },

  async getCustomer(id: string): Promise<CustomerOut | null> {
    return withFallback(() => request<CustomerOut>(`/customers/${encodeURIComponent(id)}`), () => MOCK_CUSTOMER_DETAIL(id));
  },

  async getCustomerExplain(id: string): Promise<CustomerExplain> {
    return withFallback(() => request<CustomerExplain>(`/customers/${encodeURIComponent(id)}/explain`), () =>
      MOCK_CUSTOMER_DETAIL(id)?.risk_level === "high" ? MOCK_EXPLAIN_HIGH : MOCK_EXPLAIN_LOW,
    );
  },

  // ------------------------------------------------------------- prediction
  async predict(input: PredictionInput): Promise<PredictionResponse> {
    return withFallback(
      () => request<PredictionResponse>("/predict", { method: "POST", body: JSON.stringify(input) }),
      () =>
        MOCK_CUSTOMER_DETAIL(input.customer_id)?.risk_level === "high"
          ? MOCK_PREDICTION_HIGH
          : { ...MOCK_PREDICTION_LOW, customer_id: input.customer_id },
    );
  },

  async predictBatch(customers: PredictionInput[]): Promise<{ predictions: PredictionResponse[]; summary: { count: number; mean_probability: number; high_risk: number; expected_churners: number } }> {
    return withFallback(
      () =>
        request("/predict/batch", {
          method: "POST",
          body: JSON.stringify({ customers }),
        }),
      () => ({
        predictions: customers.map((c) => (c.total_charges > 0 && c.tenure > 18 ? MOCK_PREDICTION_LOW : MOCK_PREDICTION_HIGH)),
        summary: {
          count: customers.length,
          mean_probability: 0.42,
          high_risk: Math.floor(customers.length * 0.2),
          expected_churners: Math.floor(customers.length * 0.25),
        },
      }),
    );
  },

  async explain(input: PredictionInput): Promise<CustomerExplain> {
    return withFallback(
      () => request<CustomerExplain>("/explain", { method: "POST", body: JSON.stringify(input) }),
      () => (input.tenure > 18 ? MOCK_EXPLAIN_LOW : MOCK_EXPLAIN_HIGH),
    );
  },

  // ------------------------------------------------------------- model ops
  async getMetrics(): Promise<ModelMetrics> {
    return withFallback(() => request<ModelMetrics>("/metrics"), () => MOCK_METRICS);
  },

  async getModelStatus(): Promise<ModelStatus> {
    return withFallback(() => request<ModelStatus>("/model/status"), () => MOCK_MODEL_STATUS);
  },

  async getFeatureCatalogue(): Promise<FeatureCatalogue> {
    return withFallback(
      async () => (await request<{ catalogue: FeatureCatalogue }>("/feature-catalogue")).catalogue,
      () => FEATURE_CATALOGUE,
    );
  },
};

export { DEFAULT_INPUT };