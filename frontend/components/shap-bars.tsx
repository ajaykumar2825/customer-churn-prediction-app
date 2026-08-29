"use client";

import { cn } from "@/lib/utils";

interface Item {
  feature: string;
  value: number;
}

/** Centered zero-axis SHAP waterfall bars. */
export function ImportBars({ items }: { items: Item[] }) {
  const max = Math.max(...items.map((i) => Math.abs(i.value)), 0.0001);
  const threshold = max * 0.55;
  const above = items.filter((i) => Math.abs(i.value) >= threshold);
  const below = items.filter((i) => Math.abs(i.value) < threshold);
  const stacked = above.length ? [...above, { feature: "...", value: below.reduce((s, i) => s + i.value, 0) }] : items;

  return (
    <div className="space-y-2">
      {stacked.slice(0, 7).map((item, idx) => {
        const positive = item.value >= 0;
        const width = (Math.abs(item.value) / max) * 100;
        return (
          <div key={`${item.feature}-${idx}`} className="flex items-center gap-2">
            <span className="w-28 shrink-0 truncate text-right text-[11px] text-muted-foreground">
              {item.feature === "..." ? item.feature : item.feature.replace(/_/g, " · ")}
            </span>
            <div className="relative h-5 flex-1">
              <div className="absolute inset-y-0 left-1/2 w-px bg-border" />
              <div
                className={cn(
                  "absolute inset-y-0 rounded",
                  positive ? "right-1/2 bg-gradient-to-l from-danger/80 to-danger" : "left-1/2 bg-gradient-to-r from-success to-success/70",
                )}
                style={{ width: `${width / 2}%` }}
              />
            </div>
            <span className={cn("w-16 shrink-0 font-mono text-[11px] font-semibold", positive ? "text-danger" : "text-success")}>
              {item.value >= 0 ? "+" : ""}
              {item.value.toFixed(3)}
            </span>
          </div>
        );
      })}
    </div>
  );
}