"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Lightweight ScrollArea — uses native overflow with custom-styled
 * scrollbars. Drop-in compatible with `@/components/ui/scroll-area` so the
 * codebase can switch to the Radix-based shadcn variant later by adding
 * `@radix-ui/react-scroll-area` and re-exporting from this path.
 */
export const ScrollArea = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "relative overflow-y-auto overflow-x-hidden [scrollbar-width:thin] [scrollbar-color:hsl(var(--muted-foreground))_transparent]",
      className
    )}
    {...props}
  >
    {children}
  </div>
));
ScrollArea.displayName = "ScrollArea";
