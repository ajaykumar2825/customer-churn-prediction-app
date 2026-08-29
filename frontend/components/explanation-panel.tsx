"use client";

import { Flame, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ImportBars } from "@/components/shap-bars";
import type { Explanation, RiskLevel } from "@/types";
import { cn, formatPercent } from "@/lib/utils";

export function ExplanationPanel({
  explanation,
  probability,
  riskLevel,
  className,
}: {
  explanation: Explanation | null;
  probability: number;
  riskLevel: RiskLevel;
  className?: string;
}) {
  if (!explanation) {
    return (
      <Card className={cn("animate-fade-up", className)}>
        <CardContent className="p-6 text-sm text-muted-foreground">
          No explanation available for this profile yet — run a prediction first.
        </CardContent>
      </Card>
    );
  }

  const high = riskLevel === "high";
  const contributing = explanation.contributions ?? [];

  return (
    <Card className={cn("animate-fade-up overflow-hidden", className)}>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          {high ? <Flame className="size-4 text-danger" /> : <ShieldAlert className="size-4 text-success" />}
          Why this prediction
        </CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant={high ? "destructive" : "success"}>
            {Math.round(probability * 100)}% churn risk
          </Badge>
          <Badge variant="outline" className="font-mono">
            base {explanation.base_value !== null ? formatPercent(explanation.base_value, 1) : "—"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <ImportBars items={contributing.slice(0, 10)} />

        <div className="rounded-xl border border-border bg-secondary/40 p-4">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Top drivers
          </p>
          <div className="flex flex-wrap gap-2">
            {explanation.top_factors.map((f) => (
              <span key={f.feature} className="rounded-lg border border-border bg-card px-2.5 py-1 text-[11px]">
                {f.feature.replace(/_/g, " · ")}
                <span className={cn("ml-1.5 font-mono font-semibold", f.value >= 0 ? "text-danger" : "text-success")}>
                  {f.value >= 0 ? "+" : ""}
                  {f.value.toFixed(3)}
                </span>
              </span>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}