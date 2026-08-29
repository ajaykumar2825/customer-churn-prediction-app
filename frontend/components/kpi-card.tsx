import { ArrowDownRight, ArrowUpRight, type LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface KpiProps {
  label: string;
  value: string;
  icon: LucideIcon;
  /** Signed fraction, e.g. -0.034 for a 3.4% decline. */
  delta?: number | null;
  deltaLabel?: string;
  hint?: string;
  accent?: "primary" | "cyan" | "success" | "warning" | "danger";
}

const ACCENTS: Record<string, string> = {
  primary: "from-primary/25 to-primary/5 text-primary",
  cyan: "from-cyan/25 to-cyan/5 text-cyan",
  success: "from-success/25 to-success/5 text-success",
  warning: "from-warning/25 to-warning/5 text-warning",
  danger: "from-danger/25 to-danger/5 text-danger",
};

export function KpiCard({ label, value, icon: Icon, delta, deltaLabel, hint, accent = "primary" }: KpiProps) {
  const improving = delta == null ? null : delta <= 0;
  const showDelta = delta !== undefined && delta !== null;
  return (
    <Card className="animate-fade-up overflow-hidden transition-shadow hover:shadow-glow">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-3">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</p>
          <div className={cn("grid size-9 shrink-0 place-items-center rounded-xl bg-gradient-to-br", ACCENTS[accent])}>
            <Icon className="size-[18px]" />
          </div>
        </div>

        <p className="mt-3 text-[26px] font-bold leading-none tracking-tight">{value}</p>

        <div className="mt-3 flex items-center gap-2">
          {showDelta ? (
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold",
                improving ? "bg-success/15 text-success" : "bg-danger/15 text-danger",
              )}
            >
              {improving ? <ArrowDownRight className="size-3" /> : <ArrowUpRight className="size-3" />}
              {Math.abs(delta * 100).toFixed(1)}%
            </span>
          ) : null}
          {deltaLabel && <span className="text-[11px] text-muted-foreground">{deltaLabel}</span>}
        </div>

        {hint && <p className="mt-2 text-[11px] text-muted-foreground/80">{hint}</p>}
      </CardContent>
    </Card>
  );
}