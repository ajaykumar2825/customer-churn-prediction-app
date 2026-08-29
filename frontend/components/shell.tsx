"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BarChart3,
  Bell,
  Gauge,
  Landmark,
  LayoutDashboard,
  ScanFace,
  Search,
  Sparkles,
  Users,
} from "lucide-react";

import { Logo } from "@/components/logo";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { fallbackNotice } from "@/lib/api";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/customers", label: "Customers", icon: Users },
  { href: "/predict", label: "Predict", icon: Sparkles },
  { href: "/explain", label: "Explain Risk", icon: ScanFace },
  { href: "/models", label: "Models", icon: Gauge },
  { href: "/strategy", label: "Strategy", icon: Landmark },
];

function NavItem({ href, label, icon: Icon }: { href: string; label: string; icon: typeof LayoutDashboard }) {
  const pathname = usePathname();
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Link
          href={href}
          className={cn(
            "relative flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-all",
            active
              ? "bg-primary/15 text-primary"
              : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
          )}
        >
          {active && <span className="absolute -left-3 h-6 w-1 rounded-r-full bg-primary shadow-glow" />}
          <Icon className="size-[18px] shrink-0" strokeWidth={2} />
          <span className="hidden lg:inline">{label}</span>
        </Link>
      </TooltipTrigger>
      <TooltipContent side="right" className="lg:hidden">
        {label}
      </TooltipContent>
    </Tooltip>
  );
}

function DemoBanner() {
  const notice = fallbackNotice();
  if (!notice) return null;
  return (
    <div className="mx-3 mt-3 flex items-center gap-2 rounded-lg border border-warning/30 bg-warning/10 px-3 py-2 text-[11px] text-warning">
      <Bell className="size-3.5 shrink-0" />
      <span>Offline preview — API at <code className="rounded bg-black/30 px-1">{notice.apiUrl}</code> unreachable.</span>
    </div>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-40 flex w-[68px] flex-col gap-1 border-r border-border bg-card/40 px-3 py-5 backdrop-blur lg:w-[236px]">
        <div className="mb-6 px-1"><Logo /></div>
        <nav className="flex flex-1 flex-col gap-1">
          {NAV.map((item) => (
            <NavItem key={item.href} {...item} />
          ))}
        </nav>
        <div className="px-1">
          <Badge variant="cyan" className="w-full justify-center text-[10px] uppercase tracking-widest">
            <Activity className="size-3" /> Model Live
          </Badge>
        </div>
        <DemoBanner />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col lg:pl-[236px]">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur-lg">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Search className="size-4" />
            <span className="hidden sm:inline">Churn prediction platform — gradient-boosted · SHAP-explainable</span>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="hidden md:inline-flex">
              <span className="mr-1.5 size-1.5 animate-pulse rounded-full bg-success" />
              v1.0.0
            </Badge>
            <div className="grid size-9 place-items-center rounded-full bg-gradient-to-br from-primary/60 to-cyan/60 text-xs font-bold">
              CX
            </div>
          </div>
        </header>

        <main className="min-w-0 flex-1 px-6 py-8 lg:px-8">{children}</main>

        <footer className="border-t border-border px-6 py-4 text-center text-[11px] text-muted-foreground">
          Churn Intelligence · Built with XGBoost + SHAP + FastAPI + Next.js — © 2026 Retention Analytics
        </footer>
      </div>
    </div>
  );
}