"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { api, toApiError } from "@/lib/api";

type Row = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  chat_session_count?: number;
  itinerary_count?: number;
};

export default function AdminUsersPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [q, setQ] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const params = new URLSearchParams();
      if (q.trim()) params.set("q", q.trim());
      const { data } = await api.get<{ results?: Row[] }>(
        `/api/v1/admin/users/?${params}`
      );
      setRows(data.results ?? (data as unknown as Row[]));
    } catch (e) {
      setErr(toApiError(e).message);
    }
  }, [q]);

  useEffect(() => {
    load();
  }, [load]);

  async function setRole(id: number, role: string) {
    setBusyId(id);
    try {
      await api.post(`/api/v1/admin/users/${id}/set-role/`, { role });
      await load();
    } catch (e) {
      setErr(toApiError(e).message);
    } finally {
      setBusyId(null);
    }
  }

  async function toggleActive(id: number, is_active: boolean) {
    setBusyId(id);
    try {
      await api.post(`/api/v1/admin/users/${id}/set-active/`, { is_active });
      await load();
    } catch (e) {
      setErr(toApiError(e).message);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white">Users</h1>
          <p className="text-sm text-slate-400">
            Search by email or name. Adjust roles and account status.
          </p>
        </div>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search…"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500"
          />
          <button
            type="button"
            onClick={() => load()}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
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
        <table className="w-full min-w-[640px] text-left text-sm md:min-w-[720px]">
          <thead className="border-b border-slate-800 bg-slate-900/80 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="hidden px-4 py-3 sm:table-cell">Active</th>
              <th className="hidden px-4 py-3 md:table-cell">Chats / trips</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.map((u) => (
              <tr key={u.id} className="bg-slate-950/40">
                <td className="px-4 py-3 text-slate-200">
                  <div className="font-medium">{u.email}</div>
                  <div className="text-xs text-slate-500">{u.full_name}</div>
                </td>
                <td className="px-4 py-3 text-slate-300">{u.role}</td>
                <td className="hidden px-4 py-3 sm:table-cell">
                  {u.is_active ? (
                    <span className="text-emerald-400">Yes</span>
                  ) : (
                    <span className="text-red-400">No</span>
                  )}
                </td>
                <td className="hidden px-4 py-3 text-slate-400 md:table-cell">
                  {u.chat_session_count ?? 0} / {u.itinerary_count ?? 0}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-2">
                    {busyId === u.id && (
                      <Loader2 className="h-4 w-4 animate-spin text-emerald-400" />
                    )}
                    <select
                      defaultValue={u.role}
                      disabled={busyId === u.id}
                      onChange={(e) => setRole(u.id, e.target.value)}
                      className="rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-white"
                    >
                      <option value="tourist">tourist</option>
                      <option value="editor">editor</option>
                      <option value="admin">admin</option>
                    </select>
                    <button
                      type="button"
                      disabled={busyId === u.id}
                      onClick={() => toggleActive(u.id, !u.is_active)}
                      className="rounded border border-slate-600 px-2 py-1 text-xs text-slate-200 hover:bg-slate-800"
                    >
                      {u.is_active ? "Deactivate" : "Restore"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
