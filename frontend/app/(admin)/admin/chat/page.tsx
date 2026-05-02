"use client";

import { useCallback, useEffect, useState } from "react";
import { api, toApiError } from "@/lib/api";

type SessionRow = {
  id: number;
  user_email: string;
  title: string | null;
  language: string;
  last_activity_at: string;
  message_count?: number;
};

type Msg = {
  id: number;
  role: string;
  content: string;
  created_at: string;
};

export default function AdminChatPage() {
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [err, setErr] = useState<string | null>(null);

  const loadSessions = useCallback(async () => {
    setErr(null);
    try {
      const { data } = await api.get<{ results?: SessionRow[] }>(
        "/api/v1/admin/chat-sessions/"
      );
      setSessions(data.results ?? (data as unknown as SessionRow[]));
    } catch (e) {
      setErr(toApiError(e).message);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  async function loadMessages(id: number) {
    setSelected(id);
    setErr(null);
    try {
      const { data } = await api.get(`/api/v1/admin/chat-sessions/${id}/messages/`);
      setMsgs(Array.isArray(data) ? (data as Msg[]) : []);
    } catch (e) {
      setErr(toApiError(e).message);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Chat sessions</h1>
        <p className="text-sm text-slate-400">
          Read-only access for customer support.
        </p>
      </div>

      {err && (
        <p className="rounded-lg bg-red-950/50 px-3 py-2 text-sm text-red-200">
          {err}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <div className="max-h-[70vh] overflow-auto rounded-2xl border border-slate-800">
            <ul className="divide-y divide-slate-800 text-sm">
              {sessions.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    onClick={() => loadMessages(s.id)}
                    className={`flex w-full flex-col items-start px-4 py-3 text-left hover:bg-slate-900 ${
                      selected === s.id ? "bg-slate-900/80" : ""
                    }`}
                  >
                    <span className="font-medium text-slate-100">
                      {s.title || "(untitled)"}
                    </span>
                    <span className="text-xs text-slate-500">{s.user_email}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="lg:col-span-3">
          <div className="max-h-[70vh] space-y-3 overflow-auto rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
            {!selected && (
              <p className="text-sm text-slate-500">Select a session.</p>
            )}
            {msgs.map((m) => (
              <div
                key={m.id}
                className={`rounded-xl border px-3 py-2 text-sm ${
                  m.role === "user"
                    ? "border-slate-700 bg-slate-900/60 text-slate-200"
                    : "border-emerald-900/40 bg-emerald-950/20 text-slate-100"
                }`}
              >
                <span className="text-[10px] font-bold uppercase text-slate-500">
                  {m.role}
                </span>
                <p className="mt-1 whitespace-pre-wrap">{m.content}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
