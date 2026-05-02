"use client";

import Link from "next/link";
import { useState } from "react";
import { Loader2, Mail } from "lucide-react";
import { AuthCard } from "@/components/auth/auth-card";
import { api, toApiError } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await api.post("/api/v1/auth/password/reset/", {
        email: email.trim().toLowerCase(),
      });
      setDone(true);
    } catch (e) {
      setErr(toApiError(e).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard
      title="Reset password"
      subtitle={
        done
          ? "Check your inbox for a reset link (and spam folder)."
          : "We will email you a secure link if an account exists."
      }
      footer={
        <p>
          Remembered it?{" "}
          <Link href="/login" className="font-semibold text-jade-700 hover:underline">
            Sign in
          </Link>
        </p>
      }
    >
      {done ? (
        <p className="text-sm text-ink-600">
          For privacy we always show this confirmation, even when no account matches.
        </p>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block">
            <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-kicker text-ink-600">
              <Mail className="h-3 w-3" /> Email
            </span>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
              placeholder="you@example.com"
            />
          </label>
          {err && (
            <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
              {err}
            </p>
          )}
          <button
            type="submit"
            disabled={busy}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-jade-700 py-3 text-sm font-semibold text-white hover:bg-jade-800 disabled:opacity-60"
          >
            {busy && <Loader2 className="h-4 w-4 animate-spin" />}
            Send reset link
          </button>
        </form>
      )}
    </AuthCard>
  );
}
