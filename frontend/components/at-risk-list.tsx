"use client";

import Link from "next/link";
import { ArrowUpRight, TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface AtRiskRow {
  customer_id: string;
  probability: number;
  contract: string;
  monthly_charges: number;
  payment_method: string;
}

export function AtRiskList({ rows }: { rows: AtRiskRow[] }) {
  return (
    <Card className="animate-fade-up">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="size-4 text-danger" />
          Priority Watchlist
        </CardTitle>
        <Link href="/customers" className="flex items-center gap-1 text-xs text-primary hover:underline">
          View all <ArrowUpRight className="size-3" />
        </Link>
      </CardHeader>
      <CardContent className="space-y-1">
        {rows.map((row) => (
          <Link
            key={row.customer_id}
            href={`/customers/${row.customer_id}`}
            className="flex items-center gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-accent/50"
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{row.customer_id}</p>
              <p className="truncate text-[11px] text-muted-foreground">
                {row.contract} · {row.payment_method}
              </p>
            </div>
            <p className="text-xs font-semibold text-muted-foreground">${row.monthly_charges.toFixed(2)}/mo</p>
            <Badge variant="destructive" className="w-[72px] justify-center font-mono">
              {Math.round(row.probability * 100)}%
            </Badge>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}