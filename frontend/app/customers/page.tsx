"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ArrowUpDown, Download, Search } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { RiskBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { CustomersPage } from "@/types";

const RISK_OPTIONS = [
  { value: "all", label: "All risk" },
  { value: "low", label: "Low risk" },
  { value: "medium", label: "Medium risk" },
  { value: "high", label: "High risk" },
];

export default function CustomersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState("all");
  const [sortBy, setSortBy] = useState("churn_probability");
  const [ascending, setAscending] = useState(false);
  const [data, setData] = useState<CustomersPage | null>(null);
  const [loading, setLoading] = useState(true);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(
    async (overrides: { search?: string; risk?: string; sortBy?: string; ascending?: boolean; page?: number } = {}) => {
      setLoading(true);
      const result = await api.getCustomers({
        search: overrides.search ?? search,
        risk: overrides.risk ?? (risk === "all" ? undefined : risk),
        sort_by: overrides.sortBy ?? sortBy,
        ascending: overrides.ascending ?? ascending,
        page: overrides.page ?? page,
        page_size: 8,
      });
      setData(result);
      setLoading(false);
    },
    [search, risk, sortBy, ascending, page],
  );

  useEffect(() => {
    load();
  }, [load]);

  const onSearch = (value: string) => {
    setSearch(value);
    setPage(1);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => load({ search: value, page: 1 }), 300);
  };

  const onRisk = (value: string) => {
    setRisk(value);
    setPage(1);
    load({ risk: value === "all" ? undefined : value, page: 1 });
  };

  const onSort = (column: string) => {
    const next = sortBy === column ? !ascending : true;
    setSortBy(column);
    setAscending(next);
    load({ sortBy: column, ascending: next });
  };

  const exportUrl = useMemo(() => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (risk !== "all") params.set("risk", risk);
    params.set("page_size", "10000");
    return `${api.baseUrl}/customers/export?${params.toString()}`;
  }, [search, risk]);

  const items = data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Customer Base"
        description="Search, filter and rank every customer by predicted churn risk."
        actions={
          <Button variant="outline" asChild>
            <a href={exportUrl} download="customers.csv">
              <Download className="size-4" /> Export CSV
            </a>
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative min-w-64 flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search by customer ID…" value={search} onChange={(e) => onSearch(e.target.value)} className="pl-9" />
        </div>
        <div className="w-44">
          <Select value={risk} onValueChange={onRisk}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {RISK_OPTIONS.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <span className="text-xs text-muted-foreground">
          {data ? `${data.total.toLocaleString()} customers` : "…"}
        </span>
      </div>

      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-card">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Customer</TableHead>
              <TableHead className="cursor-pointer select-none" onClick={() => onSort("tenure")}>Tenure <ArrowUpDown className="inline size-3" /></TableHead>
              <TableHead>Contract</TableHead>
              <TableHead>Payment</TableHead>
              <TableHead className="cursor-pointer select-none text-right" onClick={() => onSort("monthly_charges")}>Monthly <ArrowUpDown className="inline size-3" /></TableHead>
              <TableHead className="cursor-pointer select-none text-right" onClick={() => onSort("churn_probability")}>Risk <ArrowUpDown className="inline size-3" /></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading
              ? Array.from({ length: 6 }).map((_, i) => (
                  <TableRow key={i} className="hover:bg-transparent">
                    {Array.from({ length: 6 }).map((__, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              : items.map((c) => (
                  <TableRow key={c.customer_id}>
                    <TableCell>
                      <Link href={`/customers/${c.customer_id}`} className="block">
                        <p className="font-mono text-sm font-semibold hover:text-primary">{c.customer_id}</p>
                        <p className="text-[11px] text-muted-foreground">
                          {c.tenure} mo · {c.internet_service || "No internet"}
                        </p>
                      </Link>
                    </TableCell>
                    <TableCell>{c.tenure}</TableCell>
                    <TableCell>{c.contract}</TableCell>
                    <TableCell className="text-muted-foreground">{c.payment_method}</TableCell>
                    <TableCell className="text-right font-mono">{formatCurrency(c.monthly_charges)}</TableCell>
                    <TableCell className="text-right">
                      <RiskBadge level={c.risk_level} probability={c.churn_probability} />
                    </TableCell>
                  </TableRow>
                ))}
          </TableBody>
        </Table>
      </div>

      {data && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {data.page} of {Math.max(data.pages, 1)} · {data.total.toLocaleString()} customers
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={data.page <= 1} onClick={() => { setPage(data.page - 1); load({ page: data.page - 1 }); }}>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={data.page >= data.pages} onClick={() => { setPage(data.page + 1); load({ page: data.page + 1 }); }}>
              Next
            </Button>
          </div>
        </div>
      )}
    </>
  );
}