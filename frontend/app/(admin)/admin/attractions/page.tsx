"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, toApiError } from "@/lib/api";

type Attraction = {
  id: number;
  name: string;
  slug: string;
  district: number;
  district_name: string;
  category: string;
  trend_score: number;
};

export default function AdminAttractionsPage() {
  const [rows, setRows] = useState<Attraction[]>([]);
  const [q, setQ] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const params = new URLSearchParams();
      if (q.trim()) params.set("q", q.trim());
      const { data } = await api.get<{ results?: Attraction[] }>(
        `/api/v1/admin/attractions/?${params}`
      );
      setRows(data.results ?? (data as unknown as Attraction[]));
    } catch (e) {
      setErr(toApiError(e).message);
    }
  }, [q]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Attractions</h1>
          <p className="text-sm text-slate-400">
            Search the catalogue. Public pages open in a new context.
          </p>
        </div>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search name / slug…"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white"
          />
          <button
            type="button"
            onClick={() => load()}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Search
          </button>
        </div>
      </div>

      {err && (
        <p className="rounded-lg bg-red-950/50 px-3 py-2 text-sm text-red-200">
          {err}
        </p>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-800">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b border-slate-800 bg-slate-900/80 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">District</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Trend</th>
              <th className="px-4 py-3">Public</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.map((a) => (
              <tr key={a.id} className="bg-slate-950/40">
                <td className="px-4 py-3 font-medium text-slate-200">{a.name}</td>
                <td className="px-4 py-3 text-slate-400">{a.district_name}</td>
                <td className="px-4 py-3 text-slate-400">{a.category}</td>
                <td className="px-4 py-3 text-slate-400">{a.trend_score}</td>
                <td className="px-4 py-3">
                  <Link
                    href={`/explore/${a.slug}`}
                    className="text-emerald-400 hover:underline"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
