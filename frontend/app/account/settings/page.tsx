"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Loader2, LogOut } from "lucide-react";
import { api, toApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function SettingsPage() {
  const router = useRouter();
  const { refresh: refreshToken, clear } = useAuth();
  const [oldPw, setOldPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [newPw2, setNewPw2] = useState("");
  const [pwBusy, setPwBusy] = useState(false);
  const [pwMsg, setPwMsg] = useState<string | null>(null);
  const [pwErr, setPwErr] = useState<string | null>(null);

  async function onLogout() {
    try {
      await api.post("/api/v1/auth/logout/", { refresh: refreshToken });
    } catch {
      // ignore — we still clear local state
    }
    clear();
    router.push("/");
  }

  async function onPasswordChange(e: React.FormEvent) {
    e.preventDefault();
    setPwErr(null);
    setPwMsg(null);
    if (newPw !== newPw2) {
      setPwErr("New passwords do not match.");
      return;
    }
    setPwBusy(true);
    try {
      await api.post("/api/v1/auth/password/change/", {
        old_password: oldPw,
        new_password: newPw,
      });
      setPwMsg("Password updated.");
      setOldPw("");
      setNewPw("");
      setNewPw2("");
    } catch (err) {
      setPwErr(toApiError(err).message);
    } finally {
      setPwBusy(false);
    }
  }

  return (
    <div className="space-y-10">
      <div>
        <h1 className="display text-3xl font-medium tracking-tightest text-ink-900">
          Settings
        </h1>
        <p className="mt-1 text-sm text-ink-600">
          Change your password or sign out on this device.
        </p>
      </div>

      <section>
        <h2 className="text-lg font-semibold text-ink-900">Password</h2>
        <form onSubmit={onPasswordChange} className="mt-4 max-w-md space-y-3">
          <input
            type="password"
            autoComplete="current-password"
            placeholder="Current password"
            value={oldPw}
            onChange={(e) => setOldPw(e.target.value)}
            required
            className="w-full rounded-xl border border-border px-3 py-2 text-sm"
          />
          <input
            type="password"
            autoComplete="new-password"
            placeholder="New password"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            required
            className="w-full rounded-xl border border-border px-3 py-2 text-sm"
          />
          <input
            type="password"
            autoComplete="new-password"
            placeholder="Confirm new password"
            value={newPw2}
            onChange={(e) => setNewPw2(e.target.value)}
            required
            className="w-full rounded-xl border border-border px-3 py-2 text-sm"
          />
          {pwErr && <p className="text-sm text-red-700">{pwErr}</p>}
          {pwMsg && <p className="text-sm text-jade-700">{pwMsg}</p>}
          <button
            type="submit"
            disabled={pwBusy}
            className="inline-flex items-center gap-2 rounded-full bg-jade-700 px-6 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            {pwBusy && <Loader2 className="h-4 w-4 animate-spin" />}
            Update password
          </button>
        </form>
      </section>

      <section>
        <button
          onClick={onLogout}
          className="inline-flex items-center gap-2 rounded-full border border-red-300 bg-white px-6 py-2.5 text-sm font-semibold text-red-700 transition-colors hover:bg-red-50"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </section>
    </div>
  );
}
