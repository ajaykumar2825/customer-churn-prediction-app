"use client";

import { useEffect, useState } from "react";
import { Banknote, Flame, HandCoins, LineChart, Percent } from "lucide-react";

import { ChartCard, SegmentChurnBars } from "@/components/charts";
import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { cn, formatCurrency, formatNumber } from "@/lib/utils";
import type { RevenueBundle } from "@/types";

export default function StrategyPage() {
  const [bundle, setBundle] = useState<RevenueBundle | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    api.getRevenueBundle().then((b) => {
      if (alive) {
        setBundle(b);
        setLoading(false);
      }
    });
    return () => { alive = false; };
  }, []);

  if (loading || !bundle) return <div className="space-y-6">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-40" />)}</div>;

  const { revenue_at_risk, clv, retention_roi, segments, contract_impact } = bundle;
  const worstSegment = segments.tenure_group[0];

  return (
    <>
      <PageHeader
        title="Business Strategy"
        description="Turn model output into revenue decisions — exposure, CLV, campaign ROI and migration plays."
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Annual Revenue at Risk" value={formatCurrency(revenue_at_risk.expected_annual_loss)} icon={Banknote} accent="danger" hint={`${revenue_at_risk.percent_revenue_at_risk.toFixed(1)}% of MRR exposed`} />
        <KpiCard label="Expected Monthly Loss" value={formatCurrency(revenue_at_risk.expected_monthly_loss)} icon={Flame} accent="warning" hint={`${formatNumber(revenue_at_risk.at_risk_customers)} customers`} />
        <KpiCard label="Avg Customer LTV" value={formatCurrency(clv)} icon={LineChart} accent="primary" hint="probability-adjusted lifetime value" />
        <KpiCard label="Campaign ROI" value={`${retention_roi.roi.toFixed(1)}×`} icon={HandCoins} accent="success" deltaLabel={`${formatNumber(retention_roi.saved_customers)} saved`} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard title="Contract Migration Play" description={contract_impact.impact_note} className="xl:col-span-1">
          <div className="space-y-3">
            <PlayBar label="Average churn rate today" value={contract_impact.current_avg_churn} max={45} variant="current" />
            <PlayBar label="Average churn after migration" value={contract_impact.hypothetical_avg_churn_after_contract} max={45} variant="after" />
            <div className="flex gap-2 pt-2">
              <Badge variant="outline">MTM {contract_impact.month_to_month_share.toFixed(1)}%</Badge>
              <Badge variant="outline">1y {contract_impact.one_year_share.toFixed(1)}%</Badge>
              <Badge variant="outline">2y {contract_impact.two_year_share.toFixed(1)}%</Badge>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="Retention Campaign Economics" description="One-shot outbound campaign on p≥0.6, $35/contact, 35% save rate" className="xl:col-span-2">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <CampaignCell label="Targeted" value={formatNumber(retention_roi.customers_targeted)} accent="warning" />
            <CampaignCell label="Estimated saved" value={formatNumber(retention_roi.saved_customers)} accent="success" />
            <CampaignCell label="Campaign cost" value={formatCurrency(retention_roi.campaign_cost)} accent="muted" />
            <CampaignCell label="Recovered / yr" value={formatCurrency(retention_roi.retained_value_annual)} accent="cyan" />
          </div>
          <div className="mt-5 rounded-xl border border-border bg-secondary/40 p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="font-semibold">Return on retention spend</span>
              <span className="text-2xl font-black text-success">{retention_roi.roi.toFixed(1)}×</span>
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">
              Every dollar spent on outreach is projected to return {retention_roi.roi.toFixed(1)} dollars in retained MRR over the following year.
            </p>
          </div>
        </ChartCard>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="Where churn concentrates" description="Tenure cohorts ranked by churn rate">
          <SegmentChurnBars rows={segments.tenure_group ?? []} />
          {worstSegment && (
            <div className="mt-4 rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs text-muted-foreground">
              Highest-leverage cohort: <span className="font-semibold text-foreground">{worstSegment.segment}</span> —{" "}
              <span className="font-semibold text-danger">{worstSegment.churn_rate.toFixed(1)}%</span> churn,{" "}
              <span className="font-semibold">{formatCurrency(worstSegment.expected_monthly_loss)}/mo</span> at risk.
            </div>
          )}
        </ChartCard>

        <ChartCard title="Segment exposure table" description="Each cohort's share of predicted churn pressure">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Cohort</TableHead>
                <TableHead className="text-right">Customers</TableHead>
                <TableHead className="text-right">Churn %</TableHead>
                <TableHead className="text-right">Churners</TableHead>
                <TableHead className="text-right">Loss / mo</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(segments.tenure_group ?? []).map((r) => (
                <TableRow key={r.segment}>
                  <TableCell className="font-medium">{r.segment}</TableCell>
                  <TableCell className="text-right">{formatNumber(r.customers)}</TableCell>
                  <TableCell className="text-right">
                    <Badge variant={r.churn_rate > 33 ? "destructive" : r.churn_rate > 15 ? "warning" : "success"} className="font-mono">{r.churn_rate.toFixed(1)}%</Badge>
                  </TableCell>
                  <TableCell className="text-right">{formatNumber(r.predicted_churners)}</TableCell>
                  <TableCell className="text-right font-mono">{formatCurrency(r.expected_monthly_loss)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ChartCard>
      </div>

      <div className="mt-6 rounded-2xl border border-border bg-gradient-to-r from-primary/15 via-transparent to-cyan/15 p-6">
        <p className="flex items-center gap-2 text-lg font-bold">
          <Percent className="size-5 text-cyan" /> Executive summary
        </p>
        <p className="mt-2 max-w-4xl text-sm leading-relaxed text-muted-foreground">
          The model identifies <span className="font-semibold text-foreground">{formatNumber(revenue_at_risk.at_risk_customers)} customers</span> (p≥0.5)
          carrying <span className="font-semibold text-foreground">{formatCurrency(revenue_at_risk.expected_annual_loss)}</span> of annual revenue exposure.
          Month-to-month contracts, electronic-check payment and fiber-optic service are the strongest risk markers; new customers in their first twelve
          months are the most volatile cohort. A {formatCurrency(retention_roi.campaign_cost)} one-shot outreach campaign is projected to preserve
          around {formatCurrency(retention_roi.retained_value_annual)} of that revenue — a {retention_roi.roi.toFixed(1)}× return. Prioritise the{" "}
          <span className="font-semibold text-foreground">{worstSegment.segment}</span> cohort and the contract-migration play to compress churn structurally.
        </p>
      </div>
    </>
  );
}

function PlayBar({ label, value, max, variant }: { label: string; value: number; max: number; variant: "current" | "after" }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-mono font-semibold">{value.toFixed(1)}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className={variant === "current"
            ? "h-full rounded-full bg-gradient-to-r from-danger/70 to-danger"
            : "h-full rounded-full bg-gradient-to-r from-success/70 to-success"}
          style={{ width: `${(value / max) * 100}%` }}
        />
      </div>
    </div>
  );
}

function CampaignCell({ label, value, accent }: { label: string; value: string; accent: "warning" | "success" | "muted" | "cyan" }) {
  const tone = {
    warning: "text-warning",
    success: "text-success",
    muted: "text-foreground",
    cyan: "text-cyan",
  }[accent];
  return (
    <div className="rounded-xl border border-border bg-secondary/40 p-3 text-center">
      <p className={cn("text-xl font-bold", tone)}>{value}</p>
      <p className="mt-0.5 text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
    </div>
  );
}