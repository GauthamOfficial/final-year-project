"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { api, toApiError } from "@/lib/api";

export default function AdminKnowledgePage() {
  const [stats, setStats] = useState<{
    collection: string;
    persist_dir: string;
    chunk_count: number;
  } | null>(null);
  const [log, setLog] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .get("/api/v1/admin/corpus/")
      .then(({ data }) => setStats(data))
      .catch(() => setStats(null));
  }, []);

  async function ingest(reset: boolean) {
    setBusy(true);
    setErr(null);
    setLog(null);
    try {
      const { data } = await api.post<{ log?: string }>(
        "/api/v1/admin/ingest/",
        { reset }
      );
      setLog(data.log ?? "Done.");
      const r = await api.get("/api/v1/admin/corpus/");
      setStats(r.data);
    } catch (e) {
      setErr(toApiError(e).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Knowledge base</h1>
        <p className="text-sm text-slate-400">
          ChromaDB corpus stats and ingestion job (runs on this server).
        </p>
      </div>

      {stats && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4 text-sm">
          <p className="text-slate-400">
            Collection <span className="text-white">{stats.collection}</span>
          </p>
          <p className="mt-1 text-slate-400">
            Persist dir <span className="text-white">{stats.persist_dir}</span>
          </p>
          <p className="mt-2 text-2xl font-semibold text-emerald-400">
            {stats.chunk_count.toLocaleString()} chunks
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          disabled={busy}
          onClick={() => ingest(false)}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          Ingest / refresh chunks
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            if (
              confirm(
                "Reset clears the collection before ingest. Continue?"
              )
            )
              ingest(true);
          }}
          className="rounded-lg border border-red-800 bg-red-950/30 px-4 py-2 text-sm font-semibold text-red-200 hover:bg-red-950/50 disabled:opacity-50"
        >
          Full reset + ingest
        </button>
      </div>

      {err && (
        <p className="rounded-lg bg-red-950/50 px-3 py-2 text-sm text-red-200">
          {err}
        </p>
      )}

      {log && (
        <pre className="max-h-96 overflow-auto rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs text-slate-300">
          {log}
        </pre>
      )}
    </div>
  );
}
