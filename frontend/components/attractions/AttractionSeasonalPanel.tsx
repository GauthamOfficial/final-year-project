"use client";

import { useEffect, useState } from "react";
import {
  SeasonalChart,
  type MonthlySeasonalRow,
} from "@/components/attractions/SeasonalChart";
import { Skeleton } from "@/components/ui/skeleton";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type SeasonalResponse = {
  monthly_data: MonthlySeasonalRow[];
  best_months_names: string[];
};

export function AttractionSeasonalPanel({ slug }: { slug: string }) {
  const [data, setData] = useState<SeasonalResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const res = await fetch(
          `${API}/api/v1/attractions/${encodeURIComponent(slug)}/seasonal/`
        );
        if (!res.ok) throw new Error(`seasonal ${res.status}`);
        const json = (await res.json()) as SeasonalResponse;
        if (!cancelled) setData(json);
      } catch {
        if (!cancelled) setData(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (loading) {
    return (
      <div className="space-y-3 rounded-3xl border border-border bg-white p-6 shadow-soft md:p-8">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-10 w-full max-w-xl" />
        <Skeleton className="h-[220px] w-full rounded-xl" />
      </div>
    );
  }

  if (!data?.monthly_data?.length) {
    return null;
  }

  return (
    <SeasonalChart
      monthly_data={data.monthly_data}
      best_months_names={data.best_months_names ?? []}
    />
  );
}
