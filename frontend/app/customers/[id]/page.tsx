"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowUpRight, CheckCircle2, XCircle } from "lucide-react";

import { ChartCard } from "@/components/charts";
import { ExplanationPanel } from "@/components/explanation-panel";
import { PageHeader } from "@/components/page-header";
import { RiskBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import type { CustomerExplain, CustomerOut } from "@/types";

const ATTRIBUTES = [
  { label: "Tenure", get: (c: CustomerOut) => `${c.tenure} months` },
  { label: "Monthly charges", get: (c: CustomerOut) => formatCurrency(c.monthly_charges) },
  { label: "Total charges", get: (c: CustomerOut) => formatCurrency(c.total_charges) },
  { label: "Avg monthly charge", get: (c: CustomerOut) => formatCurrency(c.avg_monthly_charge) },
  { label: "Contract", get: (c: CustomerOut) => c.contract },
  { label: "Internet", get: (c: CustomerOut) => c.internet_service || "No internet" },
  { label: "Payment", get: (c: CustomerOut) => c.payment_method },
  { label: "Services", get: (c: CustomerOut) => `${c.total_services} add-ons` },
  { label: "Senior citizen", get: (c: CustomerOut) => (c.senior_citizen ? "Yes" : "No") },
  { label: "Paperless billing", get: (c: CustomerOut) => (c.paperless_billing ? "Yes" : "No") },
];

const SERVICES: { label: string; get: (c: CustomerOut) => boolean }[] = [
  { label: "Multiple lines", get: (c) => c.monthly_charges > 75 },
  { label: "Partner", get: (c) => c.partner },
  { label: "Dependents", get: (c) => c.dependents },
];

export default function CustomerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [customer, setCustomer] = useState<CustomerOut | null>(null);
  const [explain, setExplain] = useState<CustomerExplain | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    Promise.all([api.getCustomer(id), api.getCustomerExplain(id).catch(() => null)]).then(([c, e]) => {
      if (!alive) return;
      setCustomer(c);
      setExplain(e);
      setLoading(false);
    });
    return () => { alive = false; };
  }, [id]);

  if (loading || !customer) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-72" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Skeleton className="h-80 lg:col-span-1" />
          <Skeleton className="h-80 lg:col-span-2" />
        </div>
      </div>
    );
  }

  const pct = customer.churn_probability;
  const high = customer.risk_level === "high";

  return (
    <>
      <Button variant="ghost" size="sm" asChild className="mb-4 -ml-2 text-muted-foreground">
        <Link href="/customers">
          <ArrowLeft className="size-4" /> Back to customers
        </Link>
      </Button>

      <PageHeader
        title={customer.customer_id}
        description={`Profile and predicted churn intelligence · ${customer.contract} · ${formatCurrency(customer.monthly_charges)}/mo`}
        actions={
          <Button asChild>
            <Link href={`/predict?customer=${encodeURIComponent(customer.customer_id)}`}>
              Refine prediction <ArrowUpRight className="size-4" />
            </Link>
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Profile */}
        <Card className="animate-fade-up">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="flex items-center gap-2">
              {customer.predicted_churn ? <XCircle className="size-4 text-danger" /> : <CheckCircle2 className="size-4 text-success" />}
              Churn State
            </CardTitle>
            <RiskBadge level={customer.risk_level} probability={pct} />
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="mb-1.5 flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Predicted churn probability</span>
                <span className="font-mono font-semibold">{formatPercent(pct, 1)}</span>
              </div>
              <Progress value={pct * 100} />
              <p className={cn("mt-2 text-[11px]", high ? "text-danger" : "text-success")}>
                {high
                  ? "High risk: this account is likely to churn without intervention."
                  : customer.risk_level === "medium"
                    ? "Medium risk: monitor closely and consider proactive contact."
                    : "Low risk: account shows strong retention signals."}
              </p>
            </div>

            <div className="space-y-2 border-t border-border pt-4">
              {ATTRIBUTES.map((a) => (
                <div key={a.label} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">{a.label}</span>
                  <span className="font-medium">{a.get(customer)}</span>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-2 border-t border-border pt-4">
              {SERVICES.map((s) => (
                <div key={s.label} className={cn("rounded-lg border px-2 py-1.5 text-center text-[11px]", s.get(customer) ? "border-success/30 bg-success/10 text-success" : "border-border bg-secondary/50 text-muted-foreground")}>
                  {s.label}: {s.get(customer) ? "Yes" : "No"}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Explanation */}
        <div className="space-y-4 lg:col-span-2">
          <ExplanationPanel
            explanation={explain?.explanation ?? null}
            probability={explain?.probability ?? pct}
            riskLevel={customer.risk_level}
          />
          <ChartCard title="Revenue Impact" description="What this customer contributes if retained or lost">
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-border bg-secondary/40 p-4">
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Expected loss if churns</p>
                <p className="mt-1 text-2xl font-bold text-danger">{formatCurrency(pct * customer.monthly_charges)}<span className="text-xs font-normal text-muted-foreground"> /mo</span></p>
              </div>
              <div className="rounded-xl border border-border bg-secondary/40 p-4">
                <p className="text-[11px] uppercase tracking-wider text-muted-foreground">Lifetime value retained</p>
                <p className="mt-1 text-2xl font-bold text-success">{formatCurrency(customer.total_charges)}</p>
              </div>
            </div>
          </ChartCard>
        </div>
      </div>
    </>
  );
}