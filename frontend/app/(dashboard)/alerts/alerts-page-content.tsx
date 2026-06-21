"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ExternalLink } from "lucide-react";
import { normalizeAlertsList } from "@/lib/alerts";
import { api, toApiError } from "@/lib/api";
import { formatRelativeTime } from "@/lib/relative-time";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

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

const ORDER: AlertRow["severity"][] = ["danger", "warning", "info"];

function severityBadgeClass(s: AlertRow["severity"]) {
  if (s === "danger") return "border-destructive/40 bg-destructive/15 text-destructive";
  if (s === "warning") return "border-amber-500/50 bg-amber-50 text-amber-900 dark:bg-amber-950/40 dark:text-amber-100";
  return "border-blue-500/40 bg-blue-50 text-blue-900 dark:bg-blue-950/30 dark:text-blue-100";
}

export function AlertsPageContent() {
  const [rows, setRows] = useState<AlertRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  // True while we give the backend's background weather sync a moment to
  // populate fresh alerts after an empty first response.
  const [refreshing, setRefreshing] = useState(false);
  const cancelledRef = useRef(false);
  const retriedRef = useRef(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get<AlertRow[] | { results: AlertRow[] }>(
        "/api/v1/alerts/",
        { params: { active: "true" } }
      );
      if (cancelledRef.current) return;
      const list = normalizeAlertsList<AlertRow>(data);
      setRows(list);
      setErr(null);
      // First load came back empty: the GET just triggered a background
      // weather sync. Wait once for it to finish, then refetch.
      if (list.length === 0 && !retriedRef.current) {
        retriedRef.current = true;
        setRefreshing(true);
        setTimeout(() => {
          if (!cancelledRef.current) load().finally(() => setRefreshing(false));
        }, 8000);
      }
    } catch (e) {
      if (!cancelledRef.current) setErr(toApiError(e).message);
    } finally {
      if (!cancelledRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    cancelledRef.current = false;
    load();
    return () => {
      cancelledRef.current = true;
    };
  }, [load]);

  const grouped = useMemo(() => {
    const map: Record<string, AlertRow[]> = {
      danger: [],
      warning: [],
      info: [],
    };
    for (const r of rows) {
      if (map[r.severity]) map[r.severity].push(r);
      else map.info.push(r);
    }
    for (const k of ORDER) {
      map[k].sort(
        (a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    }
    return map;
  }, [rows]);

  if (loading) {
    return (
      <div className="container max-w-3xl py-12 text-sm text-muted-foreground">
        Loading advisories…
      </div>
    );
  }

  if (err) {
    return (
      <div className="container max-w-3xl py-12">
        <Alert variant="danger">
          <AlertDescription>{err}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="container max-w-3xl py-12">
        <Alert variant="info">
          <AlertDescription>
            {refreshing
              ? "Checking for the latest weather advisories across Sri Lanka…"
              : "No active travel advisories right now — conditions are calm across the monitored districts. This page refreshes automatically with live weather data."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container max-w-3xl space-y-10 py-10 md:py-14">
      {ORDER.map((sev) => {
        const list = grouped[sev];
        if (!list.length) return null;
        return (
          <section key={sev} className="space-y-4">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {sev === "danger"
                ? "Danger"
                : sev === "warning"
                  ? "Warning"
                  : "Info"}
            </h2>
            <div className="space-y-4">
              {list.map((a) => (
                <Card key={a.id}>
                  <CardHeader className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge
                        variant="outline"
                        className={cn("font-medium", severityBadgeClass(a.severity))}
                      >
                        {a.severity}
                      </Badge>
                      {a.district_name ? (
                        <span className="text-xs text-muted-foreground">
                          {a.district_name}
                        </span>
                      ) : null}
                    </div>
                    <CardTitle className="font-medium text-xl leading-snug">
                      {a.title}
                    </CardTitle>
                    <CardDescription className="text-sm text-muted-foreground">
                      Updated {formatRelativeTime(a.created_at)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm leading-relaxed">
                    <p>{a.body}</p>
                    {a.source_name || a.source_url ? (
                      <p className="text-xs text-muted-foreground">
                        {a.source_name ? <span>{a.source_name}</span> : null}
                        {a.source_url ? (
                          <>
                            {" · "}
                            <Link
                              href={a.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 font-medium text-jade-700 hover:underline"
                            >
                              Source
                              <ExternalLink className="h-3 w-3" />
                            </Link>
                          </>
                        ) : null}
                      </p>
                    ) : null}
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
