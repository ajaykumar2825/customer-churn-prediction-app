import Link from "next/link";
import { Compass } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="grid size-16 place-items-center rounded-2xl border border-border bg-card shadow-card">
        <Compass className="size-8 text-muted-foreground" />
      </div>
      <h1 className="mt-6 text-3xl font-black tracking-tight">404 — Page not found</h1>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        This customer record or page does not exist on the platform. Return to the command center to continue.
      </p>
      <Button asChild className="mt-6">
        <Link href="/">Back to dashboard</Link>
      </Button>
    </div>
  );
}