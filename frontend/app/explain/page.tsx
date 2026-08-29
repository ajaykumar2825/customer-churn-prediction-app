"use client";

import { useEffect, useMemo, useState } from "react";
import { FlaskConical, ScanFace } from "lucide-react";

import { ChartCard, FactorList } from "@/components/charts";
import { ExplanationPanel } from "@/components/explanation-panel";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { MOCK_CUSTOMERS } from "@/lib/mock-data";
import { api } from "@/lib/api";
import type { CustomerExplain, CustomerOut } from "@/types";

export default function ExplainPage() {
  const [selected, setSelected] = useState<string>(MOCK_CUSTOMERS[0]?.customer_id ?? "");
  const [customer, setCustomer] = useState<CustomerOut | null>(null);
  const [explain, setExplain] = useState<CustomerExplain | null>(null);
  const [loading, setLoading] = useState(false);

  const candidates = useMemo(
    () => MOCK_CUSTOMERS.sort((a, b) => b.churn_probability - a.churn_probability),
    [],
  );

  useEffect(() => {
    if (!selected) return;
    let alive = true;
    setLoading(true);
    Promise.all([api.getCustomer(selected), api.getCustomerExplain(selected)]).then(([c, e]) => {
      if (!alive) return;
      setCustomer(c);
      setExplain(e);
      setLoading(false);
    });
    return () => { alive = false; };
  }, [selected]);

  return (
    <>
      <PageHeader
        title="Explainability Lab"
        description="Local SHAP explanations: exactly why the model flags any customer."
        actions={
          <div className="flex w-64 items-center gap-2">
            <ScanFace className="size-4 text-muted-foreground" />
            <Select value={selected} onValueChange={setSelected}>
              <SelectTrigger><SelectValue placeholder="Pick a customer…" /></SelectTrigger>
              <SelectContent>
                {candidates.map((c) => (
                  <SelectItem key={c.customer_id} value={c.customer_id}>
                    {c.customer_id} · {Math.round(c.churn_probability * 100)}%
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      />

      {loading || !customer || !explain ? (
        <div className="space-y-4"><Skeleton className="h-72" /><Skeleton className="h-72" /></div>
      ) : (
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <ExplanationPanel explanation={explain.explanation} probability={explain.probability} riskLevel={explain.risk_level} />

          <div className="space-y-4">
            <ChartCard title={`Profile — ${customer.customer_id}`} description={`${customer.contract} · ${customer.internet_service || "No internet"} · ${customer.payment_method}`}>
              <div className="grid grid-cols-2 gap-3">
                <ProfileStat label="Tenure" value={`${customer.tenure} mo`} />
                <ProfileStat label="Monthly" value={`$${customer.monthly_charges.toFixed(2)}`} />
                <ProfileStat label="Total charges" value={`$${customer.total_charges.toFixed(2)}`} />
                <ProfileStat label="Services" value={`${customer.total_services}`} />
                <ProfileStat label="Paperless billing" value={customer.paperless_billing ? "Yes" : "No"} />
                <ProfileStat label="Senior citizen" value={customer.senior_citizen ? "Yes" : "No"} />
              </div>
            </ChartCard>

            <ChartCard title="Largest drivers" description="Absolute contributions, ranked">
              <FactorList items={explain.explanation.top_factors ?? []} />
            </ChartCard>

            <Button
              variant="outline"
              className="w-full gap-2"
              onClick={() => {
                const next = candidates.find((c) => c.customer_id !== selected);
                setSelected(next?.customer_id ?? selected);
              }}
            >
              <FlaskConical className="size-4" /> Compare next customer
            </Button>
          </div>
        </div>
      )}
    </>
  );
}

function ProfileStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-secondary/40 px-3 py-2.5">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-0.5 text-sm font-semibold">{value}</p>
    </div>
  );
}