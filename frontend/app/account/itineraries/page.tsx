"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Calendar, Compass, Eye, FileDown, Loader2, Trash2 } from "lucide-react";
import { api, toApiError } from "@/lib/api";

type Itinerary = {
  id: number;
  title: string;
  start_date: string;
  end_date: string;
  status: string;
  created_at: string;
  share_token: string;
  days: { id: number; day_number: number }[];
};

export default function ItinerariesPage() {
  const [items, setItems] = useState<Itinerary[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const { data } = await api.get("/api/v1/itinerary/");
      setItems(data?.results ?? data ?? []);
    } catch (e) {
      setErr(toApiError(e).message || "Could not load itineraries.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onDelete(id: number) {
    if (!confirm("Delete this itinerary?")) return;
    try {
      await api.delete(`/api/v1/itinerary/${id}/delete/`);
      setItems((s) => (s ?? []).filter((it) => it.id !== id));
    } catch (e) {
      setErr(toApiError(e).message || "Delete failed.");
    }
  }

  function pdfUrl(id: number, shareToken?: string) {
    const token = shareToken ? `?token=${encodeURIComponent(shareToken)}` : "";
    return `${api.defaults.baseURL}/api/v1/itinerary/${id}/pdf/${token}`;
  }

  return (
    <div>
      <h1 className="display text-3xl font-medium tracking-tightest text-ink-900">
        My itineraries
      </h1>
      <p className="mt-1 text-sm text-ink-600">
        Saved trip plans. Download as PDF or open to edit.
      </p>

      {err && (
        <p className="mt-6 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
          {err}
        </p>
      )}

      {items === null && (
        <div className="mt-10 flex items-center gap-2 text-sm text-ink-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading…
        </div>
      )}

      {items && items.length === 0 && (
        <div className="mt-10 rounded-3xl border border-dashed border-border p-10 text-center">
          <Compass className="mx-auto h-8 w-8 text-ink-400" />
          <p className="mt-3 text-sm text-ink-600">
            No saved itineraries yet.
          </p>
          <Link
            href="/itinerary"
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-jade-700 px-5 py-2.5 text-sm font-semibold text-white"
          >
            Build one now
          </Link>
        </div>
      )}

      {items && items.length > 0 && (
        <ul className="mt-8 grid gap-3">
          {items.map((it) => (
            <li
              key={it.id}
              className="flex items-start justify-between gap-4 rounded-2xl border border-border bg-white p-5 shadow-soft"
            >
              <div className="min-w-0">
                <p className="text-sm font-semibold text-ink-900">
                  {it.title || `Itinerary #${it.id}`}
                </p>
                <p className="mt-1 flex items-center gap-2 text-xs text-ink-500">
                  <Calendar className="h-3 w-3" />
                  {it.start_date} → {it.end_date} · {it.days.length} days
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <Link
                  href={`/account/itineraries/${it.id}`}
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-white px-3 py-1.5 text-xs font-semibold text-ink-700 transition-colors hover:bg-jade-50"
                >
                  <Eye className="h-3.5 w-3.5" /> View
                </Link>
                <a
                  href={pdfUrl(it.id, it.share_token)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-full border border-border bg-white px-3 py-1.5 text-xs font-semibold text-ink-700 transition-colors hover:bg-jade-50"
                >
                  <FileDown className="h-3.5 w-3.5" /> PDF
                </a>
                <button
                  onClick={() => onDelete(it.id)}
                  className="rounded-full p-2 text-ink-500 transition-colors hover:bg-red-50 hover:text-red-700"
                  title="Delete"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
