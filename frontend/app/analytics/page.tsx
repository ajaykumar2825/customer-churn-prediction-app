"use client";

import { useEffect, useState } from "react";
import { Layers, Percent, Users } from "lucide-react";

import { ChartCard, SegmentChurnBars } from "@/components/charts";
import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/utils";
import type { RevenueBundle, SegmentRow } from "@/types";

const DIMENSIONS = [
  { key: "contract", label: "Contract", hint: "Month-to-month is the single largest driver of churn." },
  { key: "payment_method", label: "Payment Method", hint: "Electronic check correlates strongly with churn." },
  { key: "internet_service", label: "Internet Service", hint: "Fiber-optic subscribers churn more — and carry the most revenue exposure." },
  { key: "tenure_group", label: "Tenure Cohort", hint: "Early-tenure customers are the most volatile segment." },
] as const;

export default function AnalyticsPage() {
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

  if (loading || !bundle) return <div className="grid grid-cols-1 gap-4 md:grid-cols-3">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-32" />)}</div>;

  const { segments, contract_impact } = bundle;
  const totals = {
    customers: segments.contract.reduce((s, r) => s + r.customers, 0),
    revenue: segments.contract.reduce((s, r) => s + r.expected_monthly_loss, 0),
  };

  return (
    <>
      <PageHeader
        title="Segment Analytics"
        description="Where churn concentrates across the customer base — and the revenue attached to it."
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <KpiCard label="Covered Base" value={formatNumber(totals.customers)} icon={Users} accent="primary" hint="customers segmented" />
        <KpiCard label="Share at Risk (MTM)" value={`${contract_impact.month_to_month_share.toFixed(1)}%`} icon={Percent} accent="danger" hint="month-to-month contract share" />
        <KpiCard label="Revenue Exposure" value={formatCurrency(totals.revenue)} icon={Layers} accent="warning" hint="expected monthly loss" />
      </div>

      <div className="mt-6">
        <Tabs defaultValue="contract">
          <TabsList className="mb-4 flex flex-wrap h-auto gap-1">
            {DIMENSIONS.map((d) => (
              <TabsTrigger key={d.key} value={d.key}>{d.label}</TabsTrigger>
            ))}
          </TabsList>

          {DIMENSIONS.map((d) => (
            <TabsContent key={d.key} value={d.key}>
              <DimensionBoard rows={segments[d.key] ?? []} hint={d.hint} />
            </TabsContent>
          ))}
        </Tabs>
      </div>

      <div className="mt-6 rounded-2xl border border-border bg-gradient-to-r from-danger/10 via-transparent to-cyan/10 p-5">
        <p className="text-lg font-bold">Key insight</p>
        <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
          {contract_impact.impact_note} Today {contract_impact.two_year_share.toFixed(1)}% of customers are on two-year
          terms with {contract_impact.current_avg_churn.toFixed(1)}% overall churn — a targeted migration campaign could
          take that to {contract_impact.hypothetical_avg_churn_after_contract.toFixed(1)}% or below.
        </p>
      </div>
    </>
  );
}

function DimensionBoard({ rows, hint }: { rows: SegmentRow[]; hint: string }) {
  const max = Math.max(...rows.map((r) => r.expected_monthly_loss), 1);
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <ChartCard title="Churn rate by segment" description={hint}>
        <SegmentChurnBars rows={rows} />
      </ChartCard>

      <ChartCard title="Segment detail" description="Customers, predicted churners and revenue impact">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Segment</TableHead>
              <TableHead className="text-right">Customers</TableHead>
              <TableHead className="text-right">Churn %</TableHead>
              <TableHead className="text-right">Predicted churners</TableHead>
              <TableHead className="text-right">Exp. loss/mo</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((r) => (
              <TableRow key={r.segment}>
                <TableCell className="font-medium">{r.segment}</TableCell>
                <TableCell className="text-right">{formatNumber(r.customers)}</TableCell>
                <TableCell className="text-right">
                  <Badge variant={r.churn_rate > 33 ? "destructive" : r.churn_rate > 15 ? "warning" : "success"} className="font-mono">
                    {r.churn_rate.toFixed(1)}%
                  </Badge>
                </TableCell>
                <TableCell className="text-right">{formatNumber(r.predicted_churners)}</TableCell>
                <TableCell className="text-right font-mono">
                  {formatCurrency(r.expected_monthly_loss)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <div className="mt-4 space-y-1 border-t border-border pt-4">
          {rows.map((r) => (
            <div key={`bar-${r.segment}`} className="flex items-center gap-2 text-[11px]">
              <span className="w-28 truncate text-muted-foreground">{r.segment}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
                <div className="h-full rounded-full bg-gradient-to-r from-warning to-danger" style={{ width: `${(r.expected_monthly_loss / max) * 100}%` }} />
              </div>
              <span className="w-20 text-right font-mono text-muted-foreground">{formatCurrency(r.expected_monthly_loss)}</span>
            </div>
          ))}
        </div>
      </ChartCard>
    </div>
  );
}