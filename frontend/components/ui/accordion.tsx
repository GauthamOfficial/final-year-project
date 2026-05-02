"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

type Mode = "single" | "multiple";

const Ctx = React.createContext<{
  open: Set<string>;
  toggle: (v: string) => void;
  mode: Mode;
}>({ open: new Set(), toggle: () => {}, mode: "single" });

interface AccordionProps {
  type?: Mode;
  defaultValue?: string | string[];
  className?: string;
  children: React.ReactNode;
}

export function Accordion({
  type = "single",
  defaultValue,
  className,
  children,
}: AccordionProps) {
  const initial = React.useMemo(() => {
    if (!defaultValue) return new Set<string>();
    return new Set(Array.isArray(defaultValue) ? defaultValue : [defaultValue]);
  }, [defaultValue]);

  const [open, setOpen] = React.useState<Set<string>>(initial);

  const toggle = React.useCallback(
    (v: string) =>
      setOpen((prev) => {
        const next = new Set(prev);
        if (next.has(v)) {
          next.delete(v);
        } else {
          if (type === "single") next.clear();
          next.add(v);
        }
        return next;
      }),
    [type]
  );

  return (
    <Ctx.Provider value={{ open, toggle, mode: type }}>
      <div className={cn("divide-y rounded-md border", className)}>{children}</div>
    </Ctx.Provider>
  );
}

interface ItemProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

const ItemCtx = React.createContext<string>("");

export function AccordionItem({ value, children, className }: ItemProps) {
  return (
    <ItemCtx.Provider value={value}>
      <div className={cn("px-4", className)}>{children}</div>
    </ItemCtx.Provider>
  );
}

export function AccordionTrigger({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  const value = React.useContext(ItemCtx);
  const { open, toggle } = React.useContext(Ctx);
  const isOpen = open.has(value);
  return (
    <button
      type="button"
      onClick={() => toggle(value)}
      aria-expanded={isOpen}
      className={cn(
        "flex w-full items-center justify-between py-4 text-left text-sm font-medium transition-all hover:underline",
        className
      )}
    >
      {children}
      <ChevronDown
        className={cn(
          "h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-200",
          isOpen && "rotate-180"
        )}
      />
    </button>
  );
}

export function AccordionContent({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  const value = React.useContext(ItemCtx);
  const { open } = React.useContext(Ctx);
  if (!open.has(value)) return null;
  return (
    <div className={cn("overflow-hidden pb-4 pt-0 text-sm", className)}>
      {children}
    </div>
  );
}
