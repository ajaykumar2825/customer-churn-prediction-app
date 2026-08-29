import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold transition-colors focus:outline-none",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary/15 text-primary",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        success: "border-transparent bg-success/15 text-success",
        warning: "border-transparent bg-warning/15 text-warning",
        destructive: "border-transparent bg-danger/15 text-danger",
        outline: "text-muted-foreground border-border",
        cyan: "border-transparent bg-cyan/15 text-cyan",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

/** Risk-level badge used across customer records and tables. */
function RiskBadge({ level, probability }: { level: string; probability?: number }) {
  const variant = level === "high" ? "destructive" : level === "medium" ? "warning" : "success";
  const label = level.charAt(0).toUpperCase() + level.slice(1);
  return (
    <Badge variant={variant} className="uppercase tracking-wide">
      <span className="size-1.5 rounded-full bg-current" />
      {label}
      {probability !== undefined && <span className="opacity-70">{Math.round(probability * 100)}%</span>}
    </Badge>
  );
}

export { Badge, badgeVariants, RiskBadge };