"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Loader2, Lock } from "lucide-react";
import { AuthCard } from "@/components/auth/auth-card";
import { api, toApiError } from "@/lib/api";

function ResetPasswordInner() {
  const router = useRouter();
  const params = useSearchParams();
  const uid = params.get("uid") || "";
  const token = params.get("token") || "";

  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (pw !== pw2) {
      setErr("Passwords do not match.");
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await api.post("/api/v1/auth/password/reset/confirm/", {
        uid,
        token,
        new_password: pw,
      });
      router.push("/login");
    } catch (e) {
      setErr(toApiError(e).message);
    } finally {
      setBusy(false);
    }
  }

  const invalidLink = !uid || !token;

  return (
    <AuthCard
      title="Choose a new password"
      subtitle={
        invalidLink
          ? "This link is incomplete. Open the link from your email again."
          : "Use at least 8 characters — mix letters and numbers."
      }
      footer={
        <p>
          <Link
            href="/login"
            className="font-semibold text-jade-700 hover:underline"
          >
            Back to sign in
          </Link>
        </p>
      }
    >
      {invalidLink ? null : (
        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block">
            <span className="text-xs font-semibold uppercase tracking-kicker text-ink-600">
              New password
            </span>
            <input
              type="password"
              required
              autoComplete="new-password"
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
            />
          </label>
          <label className="block">
            <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-kicker text-ink-600">
              <Lock className="h-3 w-3" /> Confirm
            </span>
            <input
              type="password"
              required
              autoComplete="new-password"
              value={pw2}
              onChange={(e) => setPw2(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
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
            Update password
          </button>
        </form>
      )}
    </AuthCard>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordInner />
    </Suspense>
  );
}
