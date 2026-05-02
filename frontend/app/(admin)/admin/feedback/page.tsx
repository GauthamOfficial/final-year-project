"use client";

import { useCallback, useEffect, useState } from "react";
import { api, toApiError } from "@/lib/api";

type Review = {
  id: number;
  attraction_name: string;
  source: string;
  sentiment_label: string;
  sentiment_score: number | null;
  body: string;
  ingested_at: string;
};

export default function AdminFeedbackPage() {
  const [rows, setRows] = useState<Review[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const { data } = await api.get<{ results?: Review[] }>(
        "/api/v1/admin/reviews/"
      );
      setRows(data.results ?? (data as unknown as Review[]));
    } catch (e) {
      setErr(toApiError(e).message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">
          Reviews & sentiment
        </h1>
        <p className="text-sm text-slate-400">
          Rows ingested into the trends pipeline (Kafka / manual).
        </p>
      </div>

      {err && (
        <p className="rounded-lg bg-red-950/50 px-3 py-2 text-sm text-red-200">
          {err}
        </p>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-800">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="border-b border-slate-800 bg-slate-900/80 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Attraction</th>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Sentiment</th>
              <th className="px-4 py-3">Snippet</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.map((r) => (
              <tr key={r.id} className="bg-slate-950/40">
                <td className="px-4 py-3 font-medium text-slate-200">
                  {r.attraction_name}
                </td>
                <td className="px-4 py-3 text-slate-400">{r.source}</td>
                <td className="px-4 py-3 text-slate-400">
                  {r.sentiment_label || "—"}
                  {r.sentiment_score != null && (
                    <span className="ml-1 text-xs">
                      ({r.sentiment_score.toFixed(2)})
                    </span>
                  )}
                </td>
                <td className="max-w-md px-4 py-3 text-slate-400">
                  <span className="line-clamp-2">{r.body}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
