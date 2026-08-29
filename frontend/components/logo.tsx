import { Activity } from "lucide-react";

import { cn } from "@/lib/utils";

export function Logo({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div className="relative grid size-9 place-items-center rounded-xl bg-gradient-to-br from-primary via-cyan to-cyan/60 shadow-glow">
        <Activity className="size-5 text-white" strokeWidth={2.5} />
        <span className="absolute inset-0 rounded-xl border border-white/20" />
      </div>
      <div className="leading-tight">
        <p className="text-sm font-bold tracking-tight">
          Churn<span className="text-primary">Intelligence</span>
        </p>
        <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">Retention OS</p>
      </div>
    </div>
  );
}