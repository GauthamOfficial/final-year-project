"use client";

import { useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";
import { api, toApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function AccountPage() {
  const { user, setUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [language, setLanguage] = useState<"en" | "si" | "ta">(
    user?.language ?? "en"
  );
  const [country, setCountry] = useState(user?.home_country ?? "");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name);
      setLanguage(user.language);
      setCountry(user.home_country);
    }
  }, [user]);

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      const { data } = await api.patch("/api/v1/auth/me/", {
        full_name: fullName,
        language,
        home_country: country,
      });
      setUser(data);
      setMsg("Saved.");
    } catch (e) {
      setMsg(toApiError(e).message || "Could not save.");
    } finally {
      setBusy(false);
    }
  }

  if (!user) return null;

  return (
    <div>
      <h1 className="display text-3xl font-medium tracking-tightest text-ink-900">
        Profile
      </h1>
      <p className="mt-1 text-sm text-ink-600">
        These details show up on the AI guide responses and your itineraries.
      </p>

      <form
        onSubmit={onSave}
        className="mt-8 max-w-xl space-y-5 rounded-3xl border border-border bg-white p-8 shadow-soft"
      >
        <Field label="Full name">
          <input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
          />
        </Field>
        <Field label="Email">
          <input
            value={user.email}
            disabled
            className="w-full rounded-xl border border-border bg-muted px-3 py-2.5 text-sm text-ink-500"
          />
        </Field>
        <Field label="Preferred language">
          <select
            value={language}
            onChange={(e) =>
              setLanguage(e.target.value as "en" | "si" | "ta")
            }
            className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
          >
            <option value="en">English</option>
            <option value="si">සිංහල (Sinhala)</option>
            <option value="ta">தமிழ் (Tamil)</option>
          </select>
        </Field>
        <Field label="Home country">
          <input
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
            placeholder="e.g. United Kingdom"
          />
        </Field>
        {msg && (
          <p className="rounded-xl bg-jade-50 px-3 py-2 text-sm text-jade-800">
            {msg}
          </p>
        )}
        <button
          type="submit"
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-full bg-jade-700 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-jade-800 disabled:opacity-60"
        >
          {busy ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          Save changes
        </button>
      </form>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-kicker text-ink-600">
        {label}
      </span>
      <div className="mt-1.5">{children}</div>
    </label>
  );
}
