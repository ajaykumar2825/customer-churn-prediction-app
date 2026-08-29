import * as React from "react";

import { cn } from "@/lib/utils";

const Progress = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { value?: number }>(
  ({ className, value = 0, ...props }, ref) => (
    <div ref={ref} role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)} {...props}>
      <div
        className="h-full w-full flex-1 rounded-full bg-gradient-to-r from-primary to-cyan transition-all duration-700 ease-out"
        style={{ transform: `translateX(-${100 - Math.max(0, Math.min(100, value))}%)` }}
      />
    </div>
  ),
);
Progress.displayName = "Progress";

export { Progress };