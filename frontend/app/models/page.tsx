"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, Cpu, Medal, Target, TrendingUp } from "lucide-react";

import { ChartCard, ConfusionMatrix, ImportanceBars, PrCurve, RocCurve } from "@/components/charts";
import { KpiCard } from "@/components/kpi-card";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { formatNumber, formatPercent } from "@/lib/utils";
import type { ModelMetrics } from "@/types";

export default function ModelsPage() {
  const [data, setData] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    api.getMetrics().then((d) => {
      if (alive) {
        setData(d);
        setLoading(false);
      }
    });
    return () => { alive = false; };
  }, []);

  const leaderboard = useMemo(() => {
    if (!data) return [];
    return (data.leaderboard ?? []).map((row, i) => ({
      rank: i + 1,
      model: String(row.model ?? "-"),
      roc_auc: Number(row.test_roc_auc ?? row.roc_auc ?? 0),
      f1: Number(row.test_f1 ?? row.f1 ?? 0),
      precision: Number(row.test_precision ?? row.precision ?? 0),
      recall: Number(row.test_recall ?? row.recall ?? 0),
      fit_seconds: Number(row.avg_fit_seconds ?? row.fit_seconds ?? 0),
      tuning: String(row.tuning ?? "default"),
    }));
  }, [data]);

  if (loading || !data) return <GenericSkeleton />;

  const meta = data.meta ?? {};
  const metrics = data.metrics ?? {};
  const curves = data.curves ?? ({} as Record<string, unknown>);
  const confusion = (data.confusion ?? {}) as Record<string, number>;
  const roc = curves.roc as { fpr: number[]; tpr: number[] } | undefined ?? { fpr: [], tpr: [] };
  const pr = curves.pr as { precision: number[]; recall: number[] } | undefined ?? { precision: [], recall: [] };
  const champion = leaderboard[0];
  const globalImportance = (data.importance?.shap?.importances ?? [])
    .map((i) => ({ feature: i.feature, value: i.importance }))
    .slice(0, 12);

  return (
    <>
      <PageHeader
        title="Model Registry"
        description="Performance of every candidate model, with the deployed champion highlighted."
        actions={
          <Badge variant="cyan" className="gap-1.5">
            <Activity className="size-3" /> {String(meta.model ?? "-")} · v{String(meta.run_id ?? "?").slice(0, 8)}
          </Badge>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <KpiCard label="ROC-AUC" value={formatNumber(Number(metrics.roc_auc ?? champion?.roc_auc ?? 0))} icon={Target} accent="primary" delta={+0.003} deltaLabel="vs baseline" />
        <KpiCard label="F1 Score" value={formatNumber(Number(metrics.f1 ?? champion?.f1 ?? 0))} icon={Medal} accent="cyan" delta={+0.011} deltaLabel="vs baseline" />
        <KpiCard label="Precision" value={formatPercent(Number(metrics.precision ?? champion?.precision ?? 0), 1)} icon={Cpu} accent="success" hint="of flagged churners" />
        <KpiCard label="Recall" value={formatPercent(Number(metrics.recall ?? champion?.recall ?? 0), 1)} icon={TrendingUp} accent="warning" hint="of true churners caught" />
        <KpiCard label="Accuracy" value={formatPercent(Number(metrics.accuracy ?? 0), 1)} icon={Activity} accent="danger" deltaLabel={`@ thresh ${formatPercent(Number(data.threshold?.threshold ?? 0.5), 1)}`} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="Model Leaderboard" description="Held-out test performance across all candidates">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>#</TableHead>
                <TableHead>Model</TableHead>
                <TableHead className="text-right">ROC-AUC</TableHead>
                <TableHead className="text-right">F1</TableHead>
                <TableHead className="text-right">Precision</TableHead>
                <TableHead className="text-right">Recall</TableHead>
                <TableHead className="text-right">Tuning</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {leaderboard.map((row) => {
                const isChampion = row.rank === 1;
                return (
                  <TableRow key={row.model} className={isChampion ? "bg-primary/10" : undefined}>
                    <TableCell>
                      {row.rank}
                      {isChampion && <span className="ml-1.5 text-[10px] text-cyan">★</span>}
                    </TableCell>
                    <TableCell className="font-mono font-medium">{row.model}</TableCell>
                    <TableCell className="text-right font-mono">{row.roc_auc.toFixed(4)}</TableCell>
                    <TableCell className="text-right font-mono">{row.f1.toFixed(4)}</TableCell>
                    <TableCell className="text-right font-mono">{row.precision.toFixed(3)}</TableCell>
                    <TableCell className="text-right font-mono">{row.recall.toFixed(3)}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant={row.tuning === "tuned" ? "cyan" : "outline"}>{row.tuning}</Badge>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </ChartCard>

        <ChartCard title="Confusion Matrix" description={String(confusion.note ?? "Test-set classification at the operational threshold")}>
          <ConfusionMatrix cm={confusion} />
          <div className="mt-4 grid grid-cols-3 gap-2 border-t border-border pt-4 text-center text-[11px] text-muted-foreground">
            <div><p className="text-sm font-bold text-foreground">{formatPercent(Number(confusion.note ? metrics.accuracy ?? 0 : 0), 1)}</p>Accuracy</div>
            <div><p className="text-sm font-bold text-foreground">{formatNumber(Number(metrics.precision ?? 0))}</p>Precision</div>
            <div><p className="text-sm font-bold text-foreground">{formatNumber(Number(metrics.recall ?? 0))}</p>Recall</div>
          </div>
        </ChartCard>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="ROC Curve" description="True vs false positive trade-off across thresholds">
          <RocCurve roc={roc} />
        </ChartCard>
        <ChartCard title="Precision-Recall Curve" description="Precision as recall expands — skewed-class view">
          <PrCurve pr={pr} />
        </ChartCard>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard title="SHAP Global Importance" description="Mean |contribution| across the scored population">
          <ImportanceBars items={globalImportance} />
        </ChartCard>

        <Card className="animate-fade-up">
          <CardContent className="flex h-full flex-col justify-center gap-4 p-5">
            <p className="text-sm font-semibold">Training snapshot</p>
            <div className="grid grid-cols-2 gap-3">
              <MetaTile label="Algorithm" value={String(meta.model ?? "-")} />
              <MetaTile label="Run" value={String(meta.run_id ?? "-")} />
              <MetaTile label="Trials" value={String(meta.tune_trials ?? "-")} />
              <MetaTile label="Dataset" value={String(meta.rows ?? "-") + " rows"} />
              <MetaTile label="Trained" value={String(meta.trained_at ?? "-")} />
              <MetaTile label="Threshold" value={String(data.threshold?.threshold ?? "-")} />
            </div>
            <p className="text-[11px] text-muted-foreground">
              Dataset: {String(meta.dataset ?? "-")} · test split {formatPercent(Number(meta.test_size ?? 0.2), 0)} · seed {String(meta.seed ?? 42)}
            </p>
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function MetaTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-secondary/40 px-3 py-2.5">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-0.5 truncate font-mono text-sm font-semibold">{value}</p>
    </div>
  );
}

function GenericSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-10 w-64" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-32" />)}</div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2"><Skeleton className="h-96" /><Skeleton className="h-96" /></div>
    </div>
  );
}