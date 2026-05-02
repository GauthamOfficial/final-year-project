"use client";

import { useCallback, useEffect, useState } from "react";
import { api, toApiError } from "@/lib/api";

type District = {
  id: number;
  name: string;
  slug: string;
  province: string;
  youtube_video_ids: string[];
  description: string;
};

export default function AdminDistrictsPage() {
  const [rows, setRows] = useState<District[]>([]);
  const [edit, setEdit] = useState<District | null>(null);
  const [ytText, setYtText] = useState("");
  const [desc, setDesc] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const { data } = await api.get<{ results?: District[] }>(
        "/api/v1/admin/districts/"
      );
      setRows(data.results ?? (data as unknown as District[]));
    } catch (e) {
      setErr(toApiError(e).message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  function openEdit(d: District) {
    setEdit(d);
    setYtText((d.youtube_video_ids || []).join(", "));
    setDesc(d.description || "");
  }

  async function save() {
    if (!edit) return;
    setSaving(true);
    setErr(null);
    try {
      const ids = ytText
        .split(/[\s,]+/)
        .map((s) => s.trim())
        .filter(Boolean);
      await api.patch(`/api/v1/admin/districts/${edit.id}/`, {
        youtube_video_ids: ids,
        description: desc,
      });
      setEdit(null);
      await load();
    } catch (e) {
      setErr(toApiError(e).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Districts</h1>
        <p className="text-sm text-slate-400">
          Curate gallery YouTube IDs and short descriptions for all 25 districts.
        </p>
      </div>

      {err && (
        <p className="rounded-lg bg-red-950/50 px-3 py-2 text-sm text-red-200">
          {err}
        </p>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-slate-800 bg-slate-900/80 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">District</th>
              <th className="px-4 py-3">Province</th>
              <th className="px-4 py-3">Videos</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.map((d) => (
              <tr key={d.id} className="bg-slate-950/40">
                <td className="px-4 py-3 font-medium text-slate-200">{d.name}</td>
                <td className="px-4 py-3 text-slate-400">{d.province}</td>
                <td className="px-4 py-3 text-slate-400">
                  {(d.youtube_video_ids || []).length} IDs
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    onClick={() => openEdit(d)}
                    className="rounded-lg border border-slate-600 px-3 py-1 text-xs text-slate-200 hover:bg-slate-800"
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {edit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-auto rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white">{edit.name}</h2>
            <label className="mt-4 block text-xs font-semibold uppercase text-slate-500">
              YouTube video IDs (comma-separated)
            </label>
            <textarea
              value={ytText}
              onChange={(e) => setYtText(e.target.value)}
              rows={3}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            />
            <label className="mt-4 block text-xs font-semibold uppercase text-slate-500">
              Description
            </label>
            <textarea
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
              rows={5}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            />
            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setEdit(null)}
                className="rounded-lg px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={save}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
