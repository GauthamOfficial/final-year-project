"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Calendar, ChevronDown, FileDown, Loader2, MapPinned } from "lucide-react";
import { api, toApiError } from "@/lib/api";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

type Stop = {
  id: number;
  stop_order: number;
  name: string;
  arrival_time: string | null;
  duration_mins: number | null;
  tip: string;
};

type Day = {
  id: number;
  day_number: number;
  district_name: string | null;
  notes: string;
  stops: Stop[];
};

type Itinerary = {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  share_token: string;
  days: Day[];
  sources?: Array<{ doc_id: string; attraction: string; relevance: number }>;
};

export default function ItineraryDetailPage() {
  const params = useParams<{ id: string }>();
  const itineraryId = useMemo(() => Number(params?.id), [params?.id]);

  const [item, setItem] = useState<Itinerary | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!itineraryId) return;
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get(`/api/v1/itinerary/${itineraryId}/`);
        if (!cancelled) setItem(data);
      } catch (e) {
        if (!cancelled) setErr(toApiError(e).message || "Could not load itinerary.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [itineraryId]);

  if (err) {
    return <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{err}</p>;
  }
  if (!item) {
    return (
      <div className="mt-6 flex items-center gap-2 text-sm text-ink-500">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading itinerary…
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="display text-3xl font-medium tracking-tightest text-ink-900">
            {item.title || `Itinerary #${item.id}`}
          </h1>
          <p className="mt-1 flex items-center gap-2 text-sm text-ink-600">
            <Calendar className="h-4 w-4" />
            {item.start_date} → {item.end_date} · {item.days.length} days
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/account/itineraries"
            className="rounded-full border border-border bg-white px-4 py-2 text-xs font-semibold text-ink-700"
          >
            Back
          </Link>
          <a
            href={`${api.defaults.baseURL}/api/v1/itinerary/${item.id}/pdf/?token=${encodeURIComponent(item.share_token)}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-full bg-jade-700 px-4 py-2 text-xs font-semibold text-white"
          >
            <FileDown className="h-3.5 w-3.5" /> Download PDF
          </a>
        </div>
      </div>

      <div className="mt-8 space-y-4">
        {item.days.map((day) => (
          <section key={day.id} className="rounded-2xl border border-border bg-white p-5 shadow-soft">
            <h2 className="text-base font-semibold text-ink-900">
              Day {day.day_number} · {day.district_name || "Unassigned"}
            </h2>
            {day.notes && <p className="mt-2 text-sm text-ink-600">{day.notes}</p>}
            <ol className="mt-4 space-y-2">
              {day.stops.map((stop) => (
                <li key={stop.id} className="rounded-xl border border-border p-3">
                  <p className="text-sm font-semibold text-ink-900">
                    {stop.stop_order}. {stop.name}
                  </p>
                  <p className="mt-1 text-xs text-ink-500">
                    <MapPinned className="mr-1 inline h-3 w-3" />
                    {stop.arrival_time?.slice(0, 5) || "Flexible"} · {stop.duration_mins || 120} mins
                  </p>
                  {stop.tip && <p className="mt-1 text-xs text-ink-600">{stop.tip}</p>}
                </li>
              ))}
            </ol>
          </section>
        ))}
      </div>

      {item.sources && item.sources.length > 0 ? (
        <Collapsible className="mt-10 max-w-3xl rounded-2xl border border-border/70 bg-muted/25 px-4 py-1 text-sm text-ink-600 shadow-sm md:px-5">
          <CollapsibleTrigger className="flex w-full items-center justify-between gap-2 py-3 text-left [&[data-state=open]_svg]:rotate-180">
            <span className="text-xs font-medium text-ink-500">AI sources used</span>
            <ChevronDown className="h-4 w-4 shrink-0 text-ink-400 transition-transform" />
          </CollapsibleTrigger>
          <CollapsibleContent className="pb-4 pt-0">
            <p className="mb-3 text-xs leading-relaxed text-ink-500">
              This itinerary was generated using {item.sources.length} verified Sri
              Lanka knowledge source{item.sources.length === 1 ? "" : "s"}.
            </p>
            <ul className="space-y-2 border-t border-border/60 pt-3">
              {item.sources.map((s) => (
                <li
                  key={`${s.doc_id}-${s.attraction}`}
                  className="flex flex-wrap items-baseline justify-between gap-2 text-xs"
                >
                  <span className="font-medium text-ink-700">
                    {s.attraction || s.doc_id}
                  </span>
                  <span className="tabular-nums text-ink-400">
                    relevance {(s.relevance * 100).toFixed(0)}%
                  </span>
                </li>
              ))}
            </ul>
          </CollapsibleContent>
        </Collapsible>
      ) : null}
    </div>
  );
}

