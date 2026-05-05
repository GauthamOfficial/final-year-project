"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Loader2, Lock, Mail } from "lucide-react";
import { AuthCard } from "@/components/auth/auth-card";
import { GoogleButton } from "@/components/auth/google-button";
import { api, toApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginInner />
    </Suspense>
  );
}

function LoginInner() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") || "/account";
  const adminMode = params.get("admin") === "1";
  const setSession = useAuth((s) => s.setSession);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const { data } = await api.post("/api/v1/auth/login/", {
        ...(adminMode
          ? { username: username.trim() }
          : { email: email.trim().toLowerCase() }),
        password,
      });
      setSession(data);
      router.push(next);
    } catch (e) {
      setErr(toApiError(e).message || "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  async function onGoogleCredential(idToken: string) {
    setBusy(true);
    setErr(null);
    try {
      const { data } = await api.post("/api/v1/auth/google/", {
        id_token: idToken,
      });
      setSession(data);
      router.push(next);
    } catch (e) {
      setErr(toApiError(e).message || "Google sign-in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard
      title="Welcome back"
      subtitle={
        adminMode
          ? "Admin sign-in requires username and password."
          : "Sign in to access your itineraries, chat history, and saved places."
      }
      footer={
        <p>
          New here?{" "}
          <Link
            href={`/signup${next ? `?next=${encodeURIComponent(next)}` : ""}`}
            className="font-semibold text-jade-700 hover:underline"
          >
            Create an account
          </Link>
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        {adminMode ? (
          <Field label="Username" icon={Mail}>
            <input
              type="text"
              required
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
              placeholder="admin"
            />
          </Field>
        ) : (
          <Field label="Email" icon={Mail}>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
              placeholder="you@example.com"
            />
          </Field>
        )}
        <Field label="Password" icon={Lock}>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
            placeholder="••••••••"
          />
        </Field>
        <div className="text-right">
          <Link
            href="/forgot-password"
            className="text-xs font-semibold text-jade-700 hover:underline"
          >
            Forgot password?
          </Link>
        </div>
        {err && (
          <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">
            {err}
          </p>
        )}
        <button
          type="submit"
          disabled={busy}
          className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-jade-700 py-3 text-sm font-semibold text-white transition-colors hover:bg-jade-800 disabled:opacity-60"
        >
          {busy && <Loader2 className="h-4 w-4 animate-spin" />}
          Sign in
        </button>
      </form>

      {!adminMode && (
        <>
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-border" />
            </div>
            <span className="relative flex justify-center text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
              <span className="bg-white px-3">or</span>
            </span>
          </div>

          <GoogleButton onCredential={onGoogleCredential} />
        </>
      )}
    </AuthCard>
  );
}

function Field({
  label,
  icon: Icon,
  children,
}: {
  label: string;
  icon?: React.ElementType;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-kicker text-ink-600">
        {Icon && <Icon className="h-3 w-3" />}
        {label}
      </span>
      <div className="mt-1.5">{children}</div>
    </label>
  );
}
