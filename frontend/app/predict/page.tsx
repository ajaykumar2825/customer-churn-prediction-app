"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Loader2, Wand2, Zap } from "lucide-react";

import { ChartCard, FactorList, RiskGauge } from "@/components/charts";
import { PageHeader } from "@/components/page-header";
import { RiskBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DEFAULT_INPUT, MOCK_CUSTOMERS } from "@/lib/mock-data";
import { api } from "@/lib/api";
import { BOOL_FEATURES, ENUM_FEATURES, FEATURE_CATALOGUE, NUMERIC_FEATURES } from "@/lib/feature-catalogue";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import type { PredictionInput, PredictionResponse } from "@/types";

export default function PredictPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <PredictPageInner />
    </Suspense>
  );
}

function PredictPageInner() {
  const searchParams = useSearchParams();
  const customerId = searchParams.get("customer") ?? "";

  const prefill = useMemo(() => {
    const found = customerId ? MOCK_CUSTOMERS.find((c) => c.customer_id === customerId) : null;
    if (!found) return { ...DEFAULT_INPUT, customer_id: customerId || DEFAULT_INPUT.customer_id };
    return {
      ...DEFAULT_INPUT,
      customer_id: found.customer_id,
      tenure: found.tenure,
      monthly_charges: found.monthly_charges,
      total_charges: found.total_charges,
      avg_monthly_charge: found.avg_monthly_charge,
      contract: found.contract,
      internet_service: found.internet_service,
      payment_method: found.payment_method,
      senior_citizen: found.senior_citizen,
      paperless_billing: found.paperless_billing,
      total_services: found.total_services,
    } satisfies PredictionInput;
  }, [customerId]);

  const [input, setInput] = useState<PredictionInput>(prefill);
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => setInput(prefill), [prefill]);

  const set = <K extends keyof PredictionInput>(key: K, value: PredictionInput[K]) => {
    setInput((prev) => ({ ...prev, [key]: value }));
    setResult(null);
  };
  const toggle = (key: string) => {
    const k = key as keyof PredictionInput;
    setInput((prev) => ({ ...prev, [k]: !(prev[k] as boolean) }));
  };

  const submit = async () => {
    setLoading(true);
    try {
      const res = await api.predict(input);
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Prediction Studio"
        description="Score any customer profile against the champion gradient-boosted model."
        actions={
          <Button onClick={submit} disabled={loading} className="gap-2">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Wand2 className="size-4" />}
            {result ? "Re-run prediction" : "Predict churn"}
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Form */}
        <Tabs defaultValue="single">
          <TabsList className="mb-4">
            <TabsTrigger value="single">Single profile</TabsTrigger>
            <TabsTrigger value="batch">Batch upload</TabsTrigger>
          </TabsList>

          <TabsContent value="single">
            <Card className="animate-fade-up">
              <CardHeader><CardTitle>Customer profile</CardTitle></CardHeader>
              <CardContent className="space-y-6">
                <FieldInput label="customer_id" value={input.customer_id} onChange={(v) => set("customer_id", v)} kind="text" />

                <div>
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Account</p>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {NUMERIC_FEATURES.map((key) => (
                      <FieldInput key={key} label={key} value={Number(input[key as keyof PredictionInput])} onChange={(v) => set(key as keyof PredictionInput, Number(v) || 0)} kind="number" />
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Plan & Billing</p>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    {ENUM_FEATURES.map((key) => (
                      <FieldEnum key={key} label={key} value={String(input[key as keyof PredictionInput])} options={FEATURE_CATALOGUE[key].options ?? []} onChange={(v) => set(key as keyof PredictionInput, v)} />
                    ))}
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Account Attributes</p>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {BOOL_FEATURES.map((key) => (
                      <ToggleField key={key} label={FEATURE_CATALOGUE[key].label} checked={Boolean(input[key as keyof PredictionInput])} onToggle={() => toggle(key)} />
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="batch">
            <BatchPanel onComplete={(rows) => { if (rows.length) setInput({ ...rows[0], customer_id: rows[0].customer_id || DEFAULT_INPUT.customer_id }); }} />
          </TabsContent>
        </Tabs>

        {/* Result */}
        <div className="space-y-4">
          {result ? (
            <>
              <Card className="animate-fade-up">
                <CardContent className="flex items-center justify-between gap-6 p-6">
                  <div>
                    <p className="text-sm text-muted-foreground">Churn probability · {result.customer_id}</p>
                    <p className={cn("text-5xl font-black tracking-tight", result.risk_level === "high" ? "text-danger" : result.risk_level === "medium" ? "text-warning" : "text-success")}>
                      {formatPercent(result.probability, 1)}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <RiskBadge level={result.risk_level} probability={result.probability} />
                      <span className="text-xs text-muted-foreground">conf {formatPercent(result.confidence, 0)}</span>
                    </div>
                  </div>
                  <RiskGauge value={result.probability} />
                </CardContent>
              </Card>

              <ChartCard title="Revenue impact" description={`Operational threshold: ${formatPercent(result.threshold, 1)}`}>
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-xl border border-border bg-secondary/40 p-4">
                    <p className="text-[11px] uppercase tracking-wider text-muted-foreground">At risk monthly</p>
                    <p className="mt-1 text-2xl font-bold text-danger">{formatCurrency(result.revenue_at_risk_monthly)}</p>
                  </div>
                  <div className="rounded-xl border border-border bg-secondary/40 p-4">
                    <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Model</p>
                    <p className="mt-1 text-lg font-bold">{result.model}<span className="ml-2 font-mono text-xs text-muted-foreground">v{result.model_version.slice(0, 8)}</span></p>
                  </div>
                </div>
                {result.retention_recommendation && (
                  <div className="mt-4 rounded-xl border border-cyan/25 bg-cyan/10 p-4 text-sm">
                    <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-cyan">Exported decision</p>
                    <p className="text-muted-foreground">{result.retention_recommendation}</p>
                  </div>
                )}
              </ChartCard>

              <ChartCard title="Why — SHAP factors" description="Top drivers of this prediction">
                <FactorList items={result.top_factors} />
              </ChartCard>
            </>
          ) : (
            <EmptyResult loading={loading} />
          )}
        </div>
      </div>
    </>
  );
}

function FieldInput({ label, value, onChange, kind }: { label: string; value: string | number; onChange: (v: string) => void; kind: "text" | "number" }) {
  return (
    <div>
      <Label className="mb-1.5 block">{FEATURE_CATALOGUE[label]?.label ?? pretty(label)}</Label>
      <Input type={kind} value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

function FieldEnum({ label, value, options, onChange }: { label: string; value: string; options: string[]; onChange: (v: string) => void }) {
  return (
    <div>
      <Label className="mb-1.5 block">{FEATURE_CATALOGUE[label]?.label ?? pretty(label)}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger><SelectValue /></SelectTrigger>
        <SelectContent>{options.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent>
      </Select>
    </div>
  );
}

function ToggleField({ label, checked, onToggle }: { label: string; checked: boolean; onToggle: () => void }) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border bg-secondary/40 px-3 py-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <Switch checked={checked} onCheckedChange={onToggle} className="ml-2" />
    </div>
  );
}

function EmptyResult({ loading }: { loading: boolean }) {
  return (
    <Card className="animate-fade-up border-dashed">
      <CardContent className="flex min-h-[420px] flex-col items-center justify-center gap-3 p-8 text-center">
        {loading ? <Loader2 className="size-10 animate-spin text-primary" /> : <Zap className="size-10 text-primary/50" />}
        <p className="text-sm font-semibold">{loading ? "Scoring profile…" : "Ready to predict"}</p>
        <p className="max-w-sm text-xs text-muted-foreground">
          Configure the customer profile on the left, then run the prediction to see the probability gauge, revenue-at-risk estimate, and SHAP explanation.
        </p>
      </CardContent>
    </Card>
  );
}

function BatchPanel({ onComplete }: { onComplete: (rows: PredictionInput[]) => void }) {
  const [text, setText] = useState("");
  const [rows, setRows] = useState<PredictionInput[]>([]);

  const parse = (value: string) => {
    setText(value);
    const parsed: PredictionInput[] = [];
    for (const line of value.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        const obj = JSON.parse(trimmed) as Partial<PredictionInput>;
        parsed.push({ ...DEFAULT_INPUT, ...obj });
      } catch {
        const cols = trimmed.split(",");
        parsed.push({
          ...DEFAULT_INPUT,
          customer_id: cols[0]?.trim() || `BATCH-${parsed.length + 1}`,
          tenure: Number(cols[1]) || 0,
          monthly_charges: Number(cols[2]) || 0,
          total_charges: Number(cols[3]) || 0,
          contract: cols[4]?.trim() || "Month-to-month",
        });
      }
    }
    setRows(parsed);
    onComplete(parsed);
  };

  const submit = async () => {
    if (!rows.length) return;
    const res = await api.predictBatch(rows);
    alert(`Batch complete: ${res.summary.count} rows · ${res.summary.expected_churners} expected churners · mean p=${res.summary.mean_probability.toFixed(3)}`);
  };

  return (
    <Card className="animate-fade-up">
      <CardHeader><CardTitle>Batch scoring</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <p className="text-xs text-muted-foreground">
          One record per line. Lines parsed as JSON objects, or CSV in order: <code className="rounded bg-secondary px-1">customer_id,tenure,monthly_charges,total_charges,contract</code>. All other fields fall back to safe defaults.
        </p>
        <textarea
          value={text}
          onChange={(e) => parse(e.target.value)}
          placeholder={`{"customer_id":"C-1001","tenure":2,"monthly_charges":89.9,"total_charges":179.8,"internet_service":"Fiber optic","contract":"Month-to-month","payment_method":"Electronic check"}`}
          className="h-48 w-full resize-none rounded-xl border border-input bg-secondary/40 p-3 font-mono text-xs text-foreground outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">{rows.length} record(s) parsed</span>
          <Button onClick={submit} disabled={!rows.length}><Zap className="size-4" /> Score batch</Button>
        </div>
      </CardContent>
    </Card>
  );
}

function pretty(key: string) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}