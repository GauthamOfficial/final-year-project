"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { normalizeAlertsList } from "@/lib/alerts";
import { api } from "@/lib/api";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "lankaguide_alerts_dismissed_ids";

type AlertRow = {
  id: number;
  district_name: string | null;
  title: string;
  body: string;
  severity: "info" | "warning" | "danger";
  source_name: string;
  source_url: string;
  created_at: string;
};

function readDismissed(): Set<number> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return new Set();
    const arr = JSON.parse(raw) as unknown;
    if (!Array.isArray(arr)) return new Set();
    return new Set(arr.map((x) => Number(x)).filter((n) => Number.isFinite(n)));
  } catch {
    return new Set();
  }
}

function writeDismissed(ids: Set<number>) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...ids]));
}

function severityOrder(s: string): number {
  if (s === "danger") return 0;
  if (s === "warning") return 1;
  if (s === "info") return 2;
  return 3;
}

export function AlertsBanner() {
  const [rows, setRows] = useState<AlertRow[]>([]);
  const [dismissed, setDismissed] = useState<Set<number>>(new Set());
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setDismissed(readDismissed());
    setHydrated(true);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get<AlertRow[] | { results: AlertRow[] }>(
          "/api/v1/alerts/",
          {
            params: { active: "true" },
          }
        );
        const list = normalizeAlertsList<AlertRow>(data);
        if (!cancelled) {
          setRows(
            [...list].sort(
              (a, b) =>
                severityOrder(a.severity) - severityOrder(b.severity) ||
                new Date(b.created_at).getTime() -
                  new Date(a.created_at).getTime()
            )
          );
        }
      } catch {
        if (!cancelled) setRows([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const { top, totalActive } = useMemo(() => {
    if (!rows.length)
      return { top: null as AlertRow | null, totalActive: 0 };
    const notHidden = rows.filter((r) => !dismissed.has(r.id));
    return {
      top: notHidden[0] ?? null,
      totalActive: rows.length,
    };
  }, [rows, dismissed]);

  const dismiss = useCallback((id: number) => {
    setDismissed((prev) => {
      const next = new Set(prev);
      next.add(id);
      writeDismissed(next);
      return next;
    });
  }, []);

  if (!hydrated || !top) return null;

  const variant =
    top.severity === "danger"
      ? "danger"
      : top.severity === "warning"
        ? "warning"
        : "info";

  return (
    <div className="border-b border-border/80 bg-background">
      <div className="container relative py-3 pr-10 md:pr-12">
        <Alert
          variant={variant}
          className={cn(
            top.severity === "danger" && "border-destructive/40 bg-destructive/10",
            top.severity === "warning" && "border-amber-500/40",
            top.severity === "info" && "border-blue-500/30 bg-blue-50/80 dark:bg-blue-950/20"
          )}
        >
          <AlertTitle className="pr-2">{top.title}</AlertTitle>
          <AlertDescription className="text-sm leading-relaxed">
            {top.body}
            {top.district_name ? (
              <span className="mt-1 block text-xs opacity-80">
                Area: {top.district_name}
              </span>
            ) : null}
            <Link
              href="/alerts"
              className="mt-2 inline-block font-medium underline-offset-4 hover:underline"
            >
              View all alerts ({totalActive})
            </Link>
          </AlertDescription>
        </Alert>
        <button
          type="button"
          aria-label="Dismiss alert"
          onClick={() => dismiss(top.id)}
          className="absolute right-2 top-3 rounded-md p-1 text-foreground/60 transition-colors hover:bg-black/5 hover:text-foreground md:right-4 md:top-4"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
