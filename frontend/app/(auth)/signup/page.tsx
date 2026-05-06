"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Loader2, Lock, Mail, User } from "lucide-react";
import { AuthCard } from "@/components/auth/auth-card";
import { GoogleButton } from "@/components/auth/google-button";
import { api, toApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function SignupPage() {
  return (
    <Suspense fallback={null}>
      <SignupInner />
    </Suspense>
  );
}

function SignupInner() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") || "/account";
  const setSession = useAuth((s) => s.setSession);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [language, setLanguage] = useState<"en" | "si" | "ta">("en");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const { data } = await api.post("/api/v1/auth/register/", {
        email: email.trim().toLowerCase(),
        password,
        password_confirm: confirm,
        full_name: fullName,
        language,
      });
      setSession(data);
      router.push(next);
    } catch (e) {
      setErr(toApiError(e).message || "Registration failed.");
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
      title="Create your account"
      subtitle="Free forever. Save itineraries, build a history, and unlock voice + translation in 3 languages."
      footer={
        <p>
          Already have an account?{" "}
          <Link
            href={`/login${next ? `?next=${encodeURIComponent(next)}` : ""}`}
            className="font-semibold text-jade-700 hover:underline"
          >
            Sign in
          </Link>
        </p>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <Field label="Full name" icon={User}>
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
            placeholder="Jane Tourist"
          />
        </Field>
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
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Field label="Password" icon={Lock}>
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
              placeholder="At least 8 chars"
            />
          </Field>
          <Field label="Confirm">
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="w-full rounded-xl border border-border bg-white px-3 py-2.5 text-sm focus:border-jade-500 focus:outline-none"
              placeholder="Re-enter password"
            />
          </Field>
        </div>
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
          Create account
        </button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-border" />
        </div>
        <span className="relative flex justify-center text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
          <span className="bg-white px-3">or</span>
        </span>
      </div>

      <GoogleButton onCredential={onGoogleCredential} text="signup_with" />
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
