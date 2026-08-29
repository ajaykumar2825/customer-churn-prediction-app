"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Landmark, RefreshCw, ShieldCheck, TrendingDown, Users, Wallet } from "lucide-react";

import { AtRiskList } from "@/components/at-risk-list";
import { ChartCard, ChurnTrendChart, RevenueTrendChart, RiskDonut } from "@/components/charts";
import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/utils";
import type { AnalyticsResponse } from "@/types";

export default function DashboardPage() {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    api.getAnalytics().then((d) => {
      if (alive) {
        setData(d);
        setLoading(false);
      }
    });
    return () => {
      alive = false;
    };
  }, []);

  if (loading || !data) return <DashboardSkeleton />;

  const { kpis, trends, risk_distribution, recent_predictions, quick_stats } = data;
  const atRisk = recent_predictions as { customer_id: string; probability: number; contract: string; monthly_charges: number; payment_method: string }[];

  return (
    <>
      <PageHeader
        title="Command Center"
        description={`Churn intelligence across ${formatNumber(kpis.total_customers)} customers in real time.`}
        actions={<Button variant="outline" size="sm" asChild><Link href="/predict"><RefreshCw className="size-4" /> New prediction</Link></Button>}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Customer Base" value={formatNumber(kpis.total_customers)} icon={Users} accent="primary" deltaLabel="active cohort" hint={`${formatNumber(kpis.active_customers)} active accounts`} />
        <KpiCard label="Churn Rate" value={formatPercent(kpis.churn_rate, 1)} icon={TrendingDown} accent="danger" delta={-0.021} deltaLabel="vs. last quarter" hint={`${formatNumber(kpis.high_risk_customers)} high-risk customers`} />
        <KpiCard label="Revenue at Risk" value={formatCurrency(kpis.revenue_at_risk)} icon={Wallet} accent="warning" deltaLabel="expected monthly loss" hint="probability-weighted MRR exposure" />
        <KpiCard label="Retention Score" value={formatPercent(kpis.retention_score, 1)} icon={ShieldCheck} accent="success" delta={+0.008} deltaLabel="vs. last quarter" hint={`avg satisfaction ${kpis.avg_satisfaction.toFixed(1)}/5`} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard title="Revenue by Tenure Cohort" description="Monthly revenue concentration across tenure brackets" className="xl:col-span-2">
          <RevenueTrendChart data={trends.revenue} />
        </ChartCard>
        <ChartCard title="Risk Distribution" description="Probability-weighted churn exposure" action={<Link href="/strategy" className="flex items-center gap-1 text-xs text-primary hover:underline">Strategy <ArrowUpRight className="size-3" /></Link>}>
          <RiskDonut data={risk_distribution} />
          <div className="mt-4 grid grid-cols-3 gap-2 border-t border-border pt-4 text-center">
            <div><p className="text-lg font-bold">{formatNumber(quick_stats.churners)}</p><p className="text-[10px] uppercase tracking-wider text-muted-foreground">Predicted churners</p></div>
            <div><p className="text-lg font-bold">{formatNumber(quick_stats.rows)}</p><p className="text-[10px] uppercase tracking-wider text-muted-foreground">Dataset rows</p></div>
            <div><p className="text-lg font-bold">{quick_stats.columns}</p><p className="text-[10px] uppercase tracking-wider text-muted-foreground">Features</p></div>
          </div>
        </ChartCard>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard title="Churn Events by Tenure" description="Historical churn concentration by tenure window" className="xl:col-span-2">
          <ChurnTrendChart data={trends.churn} />
        </ChartCard>
        <AtRiskList rows={atRisk.slice(0, 6)} />
      </div>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-border bg-gradient-to-r from-primary/10 via-transparent to-cyan/10 p-5">
        <div>
          <p className="flex items-center gap-2 text-lg font-bold"><Landmark className="size-5 text-cyan" /> Retention is a revenue strategy.</p>
          <p className="mt-1 text-sm text-muted-foreground">Over <span className="font-semibold text-success">{formatCurrency(kpis.revenue_at_risk * 12)}</span> in annual revenue is exposed this quarter. A targeted campaign recovers most of it for pennies on the dollar.</p>
        </div>
        <Button asChild><Link href="/strategy">Open Business Strategy</Link></Button>
      </div>
    </>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-10 w-64" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-32" />)}
      </div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Skeleton className="h-80 xl:col-span-2" />
        <Skeleton className="h-80" />
      </div>
    </div>
  );
}