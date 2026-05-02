"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, toApiError } from "@/lib/api";

type KpiPayload = {
  users: { total: number; active_24h: number; active_7d: number; new_30d: number };
  content: { districts: number; attractions: number; media_assets: number };
  engagement: {
    itineraries: number;
    chat_sessions: number;
    chat_messages: number;
    reviews: number;
  };
  top_attractions: Array<{ id: number; name: string; trend_score: number }>;
  sentiment_breakdown: Array<{ sentiment_label: string; count: number }>;
  recent_chats: Array<{ id: number; title: string | null; user__email: string }>;
  recent_itineraries: Array<{
    id: number;
    title: string;
    user__email: string;
    created_at: string;
  }>;
};

const PIE_COLORS = ["#34d399", "#94a3b8", "#f87171"];

export default function AdminDashboardPage() {
  const [data, setData] = useState<KpiPayload | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<KpiPayload>("/api/v1/admin/kpis/")
      .then((r) => setData(r.data))
      .catch((e) => setErr(toApiError(e).message));
  }, []);

  if (err) {
    return (
      <p className="rounded-xl border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-200">
        {err}
      </p>
    );
  }

  if (!data) {
    return <p className="text-sm text-slate-500">Loading dashboard…</p>;
  }

  const pieData = (data.sentiment_breakdown || []).map((s) => ({
    name: s.sentiment_label || "unknown",
    value: s.count,
  }));

  const barData = (data.top_attractions || []).map((a) => ({
    name: a.name.length > 18 ? a.name.slice(0, 16) + "…" : a.name,
    score: Number(a.trend_score),
  }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-white">
          Overview
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Registration, content depth, and recent traveller activity.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Tile label="Registered users" value={data.users.total} />
        <Tile label="Active (7 days)" value={data.users.active_7d} />
        <Tile label="Attractions" value={data.content.attractions} />
        <Tile label="Chat sessions" value={data.engagement.chat_sessions} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
          <h2 className="text-sm font-semibold text-slate-200">
            Top attractions by trend score
          </h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: "#0f172a",
                    border: "1px solid #334155",
                    borderRadius: 8,
                  }}
                />
                <Bar dataKey="score" fill="#34d399" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
          <h2 className="text-sm font-semibold text-slate-200">
            Review sentiment (pipeline)
          </h2>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={88}
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {pieData.map((_, i) => (
                    <Cell
                      key={i}
                      fill={PIE_COLORS[i % PIE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Feed
          title="Recent chats"
          rows={(data.recent_chats || []).map((c) => ({
            id: c.id,
            line: c.title || "(untitled)",
            sub: c.user__email,
          }))}
        />
        <Feed
          title="Recent itineraries"
          rows={(data.recent_itineraries || []).map((i) => ({
            id: i.id,
            line: i.title,
            sub: `${i.user__email} · ${new Date(i.created_at).toLocaleDateString()}`,
          }))}
        />
      </div>
    </div>
  );
}

function Tile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 px-4 py-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-3xl font-semibold tabular-nums text-white">
        {value.toLocaleString()}
      </p>
    </div>
  );
}

function Feed({
  title,
  rows,
}: {
  title: string;
  rows: Array<{ id: number; line: string; sub: string }>;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
      <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
      <ul className="mt-3 max-h-56 space-y-2 overflow-auto text-sm">
        {rows.length === 0 && (
          <li className="text-slate-500">No rows yet.</li>
        )}
        {rows.map((r) => (
          <li
            key={r.id}
            className="rounded-lg border border-slate-800/80 bg-slate-950/40 px-3 py-2"
          >
            <p className="font-medium text-slate-200">{r.line}</p>
            <p className="text-xs text-slate-500">{r.sub}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
