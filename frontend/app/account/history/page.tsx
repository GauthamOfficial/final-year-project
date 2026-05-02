"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Loader2, MessageSquare, Trash2 } from "lucide-react";
import { api, toApiError } from "@/lib/api";

type Session = {
  id: number;
  title: string;
  language: string;
  started_at: string;
  last_activity_at: string;
  message_count: number;
  preview: string;
};

export default function HistoryPage() {
  const [sessions, setSessions] = useState<Session[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const { data } = await api.get("/api/v1/chat/sessions/");
      setSessions(data?.results ?? data ?? []);
    } catch (e) {
      setErr(toApiError(e).message || "Could not load history.");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function onDelete(id: number) {
    if (!confirm("Delete this conversation?")) return;
    try {
      await api.delete(`/api/v1/chat/sessions/${id}/delete/`);
      setSessions((s) => (s ?? []).filter((it) => it.id !== id));
    } catch (e) {
      setErr(toApiError(e).message || "Delete failed.");
    }
  }

  return (
    <div>
      <h1 className="display text-3xl font-medium tracking-tightest text-ink-900">
        Chat history
      </h1>
      <p className="mt-1 text-sm text-ink-600">
        Every conversation with the AI guide, ready to resume.
      </p>

      {err && (
        <p className="mt-6 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
          {err}
        </p>
      )}

      {sessions === null && (
        <div className="mt-10 flex items-center gap-2 text-sm text-ink-500">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading…
        </div>
      )}

      {sessions && sessions.length === 0 && (
        <div className="mt-10 rounded-3xl border border-dashed border-border p-10 text-center">
          <MessageSquare className="mx-auto h-8 w-8 text-ink-400" />
          <p className="mt-3 text-sm text-ink-600">
            No conversations yet. Start chatting with the AI guide and your
            history will live here.
          </p>
          <Link
            href="/chat"
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-jade-700 px-5 py-2.5 text-sm font-semibold text-white"
          >
            Open the chat
          </Link>
        </div>
      )}

      {sessions && sessions.length > 0 && (
        <ul className="mt-8 grid gap-3">
          {sessions.map((s) => (
            <li
              key={s.id}
              className="group flex items-start justify-between gap-4 rounded-2xl border border-border bg-white p-5 shadow-soft transition-shadow hover:shadow-lift"
            >
              <Link
                href={`/chat?session=${s.id}`}
                className="flex-1 min-w-0"
              >
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-jade-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-kicker text-jade-700">
                    {s.language.toUpperCase()}
                  </span>
                  <span className="text-xs text-ink-500">
                    {new Date(s.last_activity_at).toLocaleString()}
                  </span>
                  <span className="text-xs text-ink-400">
                    · {s.message_count} messages
                  </span>
                </div>
                <p className="mt-1 truncate text-sm font-semibold text-ink-900">
                  {s.title || "Untitled conversation"}
                </p>
                <p className="mt-1 line-clamp-2 text-sm text-ink-600">
                  {s.preview || "No messages yet."}
                </p>
              </Link>
              <button
                onClick={() => onDelete(s.id)}
                className="rounded-full p-2 text-ink-500 transition-colors hover:bg-red-50 hover:text-red-700"
                title="Delete"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
