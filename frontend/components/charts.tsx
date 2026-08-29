"use client";

import { useState } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn, formatCompact, formatCurrency, formatNumber, formatPercent } from "@/lib/utils";

export const PALETTE = {
  primary: "#2563EB",
  cyan: "#06B6D4",
  success: "#10B981",
  warning: "#F59E0B",
  danger: "#EF4444",
  violet: "#8B5CF6",
  muted: "#475569",
  grid: "rgba(148,163,184,0.08)",
};

/* ------------------------------------------------ presentation primitives */

interface TooltipEntry {
  name?: string;
  value?: number;
  color?: string;
  payload?: { fill?: string };
}

const TooltipShell = ({
  active,
  payload,
  label,
  valueFormatter,
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: React.ReactNode;
  valueFormatter?: (v: number) => string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-popover/95 px-3 py-2 text-xs shadow-xl backdrop-blur">
      {label !== undefined && <p className="mb-1 font-semibold text-foreground">{label}</p>}
      {payload.map((entry, i) => (
        <p key={i} className="flex items-center gap-2 text-muted-foreground">
          <span className="size-2 rounded-full" style={{ background: entry.color ?? entry.payload?.fill }} />
          <span>{entry.name}</span>
          <span className="ml-auto pl-4 font-semibold text-foreground">
            {valueFormatter ? valueFormatter(Number(entry.value)) : formatCompact(Number(entry.value))}
          </span>
        </p>
      ))}
    </div>
  );
};

export function ChartCard({
  title,
  description,
  action,
  className,
  children,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <Card className={cn("animate-fade-up overflow-hidden", className)}>
      <CardHeader className="flex-row items-start justify-between gap-4 space-y-0">
        <div className="space-y-1">
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>
        {action}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

/* --------------------------------------------------------------- charts */

export function RevenueTrendChart({ data }: { data: { t: string; value: number }[] }) {
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 4, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id="revFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={PALETTE.primary} stopOpacity={0.5} />
              <stop offset="100%" stopColor={PALETTE.primary} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={PALETTE.grid} vertical={false} />
          <XAxis dataKey="t" axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} />
          <YAxis axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} tickFormatter={(v) => formatCompact(v)} />
          <Tooltip content={<TooltipShell valueFormatter={formatCurrency} />} />
          <Area type="monotone" dataKey="value" name="Revenue" stroke={PALETTE.primary} strokeWidth={2.5} fill="url(#revFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ChurnTrendChart({ data }: { data: { t: string; value: number }[] }) {
  return (
    <div className="h-[260px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 4, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id="churnFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={PALETTE.danger} stopOpacity={0.4} />
              <stop offset="100%" stopColor={PALETTE.danger} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={PALETTE.grid} vertical={false} />
          <XAxis dataKey="t" axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} />
          <YAxis axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} />
          <Tooltip content={<TooltipShell />} />
          <Area type="monotone" dataKey="value" name="Churned" stroke={PALETTE.danger} strokeWidth={2.5} fill="url(#churnFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function CohortLineChart({
  data,
  lines,
}: {
  data: { t: string }[];
  lines: { key: string; name: string; color: string }[];
}) {
  const [metric, setMetric] = useState("retention");
  const rows = data as { t: string; [k: string]: unknown }[];
  return (
    <div className="space-y-3">
      <Tabs value={metric} onValueChange={setMetric}>
        <TabsList>
          <TabsTrigger value="retention">Retention</TabsTrigger>
          <TabsTrigger value="churn">Churn</TabsTrigger>
        </TabsList>
      </Tabs>
      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows} margin={{ top: 8, right: 4, left: -12, bottom: 0 }}>
            <CartesianGrid stroke={PALETTE.grid} vertical={false} />
            <XAxis dataKey="t" axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
            <Tooltip content={<TooltipShell valueFormatter={(v: number) => formatPercent(v, 1)} />} />
            {lines.map((l) => (
              <Line
                key={l.key}
                type="monotone"
                dataKey={l.key}
                name={l.name}
                stroke={l.color}
                strokeWidth={2.5}
                dot={false}
                strokeDasharray={metric === "churn" ? "" : "5 3"}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function RiskDonut({ data }: { data: { label: string; value: number }[] }) {
  const COLORS = [PALETTE.success, PALETTE.warning, PALETTE.danger];
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  return (
    <div className="flex items-center gap-6">
      <div className="relative h-[190px] w-[190px] shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              innerRadius={62}
              outerRadius={86}
              paddingAngle={4}
              strokeWidth={0}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<TooltipShell />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 grid place-items-center text-center">
          <div>
            <p className="text-2xl font-bold tracking-tight">{formatNumber(total)}</p>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground">Customers</p>
          </div>
        </div>
      </div>
      <div className="space-y-3">
        {data.map((d, i) => (
          <div key={d.label} className="flex items-center gap-3">
            <span className="size-2.5 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
            <span className="text-xs text-muted-foreground">{d.label}</span>
            <span className="text-sm font-semibold">{formatNumber(d.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ImportanceBars({ items }: { items: { feature: string; value: number }[] }) {
  const max = Math.max(...items.map((i) => Math.abs(i.value)), 0.0001);
  return (
    <div className="space-y-3">
      {items.map((item) => {
        const positive = item.value >= 0;
        const width = (Math.abs(item.value) / max) * 100;
        return (
          <div key={item.feature} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="truncate text-muted-foreground">{item.feature.replace(/_/g, " · ")}</span>
              <span className={cn("font-mono font-semibold", positive ? "text-danger" : "text-success")}>
                {item.value >= 0 ? "+" : ""}
                {item.value.toFixed(4)}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
              <div
                className={cn("h-full rounded-full", positive ? "bg-gradient-to-r from-danger/70 to-danger" : "bg-gradient-to-r from-success to-success/60")}
                style={{ width: `${Math.max(width, 2)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function RocCurve({ roc }: { roc: { fpr: number[]; tpr: number[] } }) {
  const data = roc.fpr.map((fpr, i) => ({ fpr, tpr: roc.tpr[i] }));
  const diag = Array.from({ length: 21 }, (_, i) => ({ fpr: i / 20, tpr: i / 20 }));
  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 4, left: -8, bottom: 0 }}>
          <CartesianGrid stroke={PALETTE.grid} />
          <XAxis dataKey="fpr" type="number" domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} />
          <YAxis dataKey="tpr" type="number" domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} />
          <Tooltip content={<TooltipShell valueFormatter={formatPercent} />} />
          <Line data={diag} dataKey="tpr" name="Random" stroke={PALETTE.muted} strokeDasharray="4 4" dot={false} strokeWidth={1.5} />
          <Line dataKey="tpr" name="Model" stroke={PALETTE.primary} strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PrCurve({ pr }: { pr: { precision: number[]; recall: number[] } }) {
  const data = pr.recall.map((recall, i) => ({ precision: pr.precision[i], recall }));
  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 4, left: -8, bottom: 0 }}>
          <CartesianGrid stroke={PALETTE.grid} />
          <XAxis dataKey="recall" type="number" domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} />
          <YAxis dataKey="precision" type="number" domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} axisLine={false} tickLine={false} tick={{ fill: "#64748b", fontSize: 11 }} />
          <Tooltip content={<TooltipShell valueFormatter={formatPercent} />} />
          <Line dataKey="precision" name="Precision" stroke={PALETTE.cyan} strokeWidth={3} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SegmentChurnBars({ rows }: { rows: { segment: string; churn_rate: number }[] }) {
  const max = Math.max(...rows.map((r) => r.churn_rate), 1);
  return (
    <div className="space-y-3">
      {rows.map((row) => (
        <div key={row.segment} className="space-y-1">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">{row.segment}</span>
            <span className="font-semibold">{row.churn_rate.toFixed(1)}%</span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
            <div
              className={cn(
                "h-full rounded-full",
                row.churn_rate > 33 ? "bg-danger" : row.churn_rate > 15 ? "bg-warning" : "bg-success",
              )}
              style={{ width: `${(row.churn_rate / max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function FactorList({ items }: { items: { feature: string; value: number }[] }) {
  return (
    <div className="space-y-2.5">
      {items.map((item) => {
        const positive = item.value >= 0;
        return (
          <div key={item.feature} className="flex items-center justify-between gap-3 rounded-lg border border-border bg-secondary/40 px-3 py-2">
            <span className="truncate text-xs text-muted-foreground">{item.feature.replace(/_/g, " · ")}</span>
            <span className={cn("flex items-center gap-1 font-mono text-xs font-semibold", positive ? "text-danger" : "text-success")}>
              {positive ? <ArrowUp className="size-3" /> : <ArrowDown className="size-3" />}
              {item.value >= 0 ? "+" : ""}
              {item.value.toFixed(4)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export function RiskGauge({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(1, value));
  const angle = pct * 180;
  const color = pct >= 0.7 ? PALETTE.danger : pct >= 0.5 ? PALETTE.warning : PALETTE.success;
  return (
    <div className="relative h-[150px] w-[190px]">
      <svg viewBox="0 0 200 110" className="h-full w-full">
        <defs>
          <linearGradient id="gauge" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={PALETTE.success} />
            <stop offset="50%" stopColor={PALETTE.warning} />
            <stop offset="100%" stopColor={PALETTE.danger} />
          </linearGradient>
        </defs>
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(148,163,184,0.15)" strokeWidth="14" strokeLinecap="round" />
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="url(#gauge)"
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${(Math.PI * 80 * angle) / 180} ${Math.PI * 80}`}
        />
        <line
          x1="100"
          y1="100"
          x2={100 + 70 * Math.cos((Math.PI * angle) / 180)}
          y2={100 - 70 * Math.sin((Math.PI * angle) / 180)}
          stroke={color}
          strokeWidth="4"
          strokeLinecap="round"
        />
        <circle cx="100" cy="100" r="6" fill={color} />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <p className="text-3xl font-bold tracking-tight" style={{ color }}>{Math.round(pct * 100)}%</p>
      </div>
    </div>
  );
}

export function ConfusionMatrix({ cm }: { cm: Record<string, number> }) {
  const { tp = 0, fp = 0, fn = 0, tn = 0 } = cm;
  const cells = [
    { label: "True Negative", value: tn, color: "text-success bg-success/10 border-success/20" },
    { label: "False Positive", value: fp, color: "text-warning bg-warning/10 border-warning/20" },
    { label: "False Negative", value: fn, color: "text-warning bg-warning/10 border-warning/20" },
    { label: "True Positive", value: tp, color: "text-success bg-success/10 border-success/20" },
  ];
  return (
    <div className="grid grid-cols-2 gap-3">
      {["Predicted No", "Predicted Yes"].map((col, ci) =>
        ["Actual No", "Actual Yes"].map((row, ri) => {
          const idx = ci + ri * 2;
          const cell = cells[idx];
          return (
            <div key={`${ci}-${ri}`} className={cn("rounded-xl border p-4", cell.color)}>
              <p className="mb-1 text-[10px] uppercase tracking-wider opacity-80">{row} · {col}</p>
              <p className="text-3xl font-bold">{formatNumber(cell.value)}</p>
            </div>
          );
        }),
      )}
    </div>
  );
}

export function ReductionBadge({ label, pct }: { label: string; pct: number }) {
  return (
    <Badge variant={pct >= 0 ? "success" : "destructive"} className="gap-1">
      {pct >= 0 ? "↓" : "↑"} {label}
    </Badge>
  );
}