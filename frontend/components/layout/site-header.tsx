"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, History, LogOut, Menu, Sparkles, User as UserIcon, X } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/explore", label: "Explore" },
  { href: "/gallery", label: "Gallery" },
  { href: "/alerts", label: "Alerts" },
  { href: "/itinerary", label: "Plan a trip" },
  { href: "/chat", label: "AI guide" },
  { href: "/translate", label: "Translate" },
];

export function SiteHeader({
  transparentTop = false,
}: {
  transparentTop?: boolean;
}) {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(!transparentTop);
  const [open, setOpen] = useState(false);
  const [activeAlertTotal, setActiveAlertTotal] = useState(0);

  useEffect(() => {
    if (!transparentTop) return;
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [transparentTop]);

  useEffect(() => {
    let cancelled = false;
    api
      .get<{ total: number }>("/api/v1/alerts/active-count/")
      .then(({ data }) => {
        if (!cancelled) setActiveAlertTotal(Number(data?.total) || 0);
      })
      .catch(() => {
        if (!cancelled) setActiveAlertTotal(0);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const transparent = transparentTop && !scrolled;

  return (
    <header
      className={cn(
        "fixed inset-x-0 top-0 z-40 transition-all duration-500",
        transparent
          ? "bg-transparent"
          : "border-b border-border/70 bg-background/85 backdrop-blur-md shadow-soft"
      )}
    >
      <div className="container flex h-16 items-center justify-between gap-6 md:h-20">
        <Logo invert={transparent} />

        <nav className="hidden items-center gap-1 lg:flex">
          {NAV.map((item) => {
            const active =
              pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative rounded-full px-3.5 py-2 text-sm font-medium transition-colors",
                  transparent
                    ? "text-white/85 hover:text-white"
                    : "text-ink-700 hover:text-ink-900",
                  active && (transparent ? "text-white" : "text-jade-700")
                )}
              >
                {item.label}
                {item.href === "/alerts" && activeAlertTotal > 0 && (
                  <Badge
                    variant="destructive"
                    className="pointer-events-none absolute -right-1 -top-1 size-2 min-h-2 min-w-2 rounded-full border-2 border-background p-0 shadow-sm"
                    aria-label={`${activeAlertTotal} active alerts`}
                  />
                )}
                {active && (
                  <span
                    className={cn(
                      "absolute inset-x-3 -bottom-0.5 h-0.5 rounded-full",
                      transparent ? "bg-saffron-400" : "bg-jade-600"
                    )}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <ProfileMenu transparent={transparent} />
        </div>

        <button
          aria-label="Open menu"
          onClick={() => setOpen((o) => !o)}
          className={cn(
            "inline-flex h-10 w-10 items-center justify-center rounded-full border lg:hidden",
            transparent
              ? "border-white/30 text-white"
              : "border-border bg-white text-ink-900"
          )}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div className="lg:hidden">
          <div className="border-t border-border bg-background/95 backdrop-blur">
            <div className="container flex flex-col gap-1 py-4">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="relative rounded-xl px-4 py-3 text-base font-medium text-ink-900 hover:bg-muted"
                >
                  {item.label}
                  {item.href === "/alerts" && activeAlertTotal > 0 && (
                    <Badge
                      variant="destructive"
                      className="pointer-events-none absolute right-3 top-3 size-2 min-h-2 min-w-2 rounded-full p-0"
                      aria-hidden
                    />
                  )}
                </Link>
              ))}
              <div className="mt-3 border-t border-border pt-3">
                <ProfileMenu transparent={false} mobile onClose={() => setOpen(false)} />
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

function ProfileMenu({
  transparent,
  mobile = false,
  onClose,
}: {
  transparent: boolean;
  mobile?: boolean;
  onClose?: () => void;
}) {
  const { user, refresh: refreshToken, clear, hydrated } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  async function logout() {
    try {
      await api.post("/api/v1/auth/logout/", { refresh: refreshToken });
    } catch {
      // ignore
    }
    clear();
    onClose?.();
    if (typeof window !== "undefined") window.location.href = "/";
  }

  if (!hydrated) {
    return null;
  }

  if (!user) {
    if (mobile) {
      return (
        <div className="flex flex-col gap-2">
          <Link
            href="/login"
            onClick={onClose}
            className="rounded-full border border-border px-4 py-2.5 text-center text-sm font-semibold text-ink-900"
          >
            Sign in
          </Link>
          <Link
            href="/signup"
            onClick={onClose}
            className="rounded-full bg-jade-700 px-4 py-2.5 text-center text-sm font-semibold text-white"
          >
            Create account
          </Link>
        </div>
      );
    }
    return (
      <>
        <Link
          href="/login"
          className={cn(
            "rounded-full px-4 py-2 text-sm font-semibold transition-colors",
            transparent
              ? "text-white/90 hover:text-white"
              : "text-ink-700 hover:text-ink-900"
          )}
        >
          Sign in
        </Link>
        <Link
          href="/signup"
          className={cn(
            "inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold shadow-soft transition-all",
            transparent
              ? "bg-white text-jade-700 hover:bg-saffron-50"
              : "bg-jade-700 text-white hover:bg-jade-800"
          )}
        >
          <Sparkles className="h-4 w-4" />
          Create account
        </Link>
      </>
    );
  }

  if (mobile) {
    return (
      <div className="flex flex-col gap-1">
        <Link
          href="/account"
          onClick={onClose}
          className="flex items-center gap-2 rounded-xl px-4 py-3 text-base font-medium text-ink-900 hover:bg-muted"
        >
          <UserIcon className="h-4 w-4" /> Profile
        </Link>
        <Link
          href="/account/history"
          onClick={onClose}
          className="flex items-center gap-2 rounded-xl px-4 py-3 text-base font-medium text-ink-900 hover:bg-muted"
        >
          <History className="h-4 w-4" /> History
        </Link>
        {user.is_admin && (
          <Link
            href="/admin"
            onClick={onClose}
            className="flex items-center gap-2 rounded-xl px-4 py-3 text-base font-medium text-jade-700 hover:bg-muted"
          >
            <Sparkles className="h-4 w-4" /> Admin dashboard
          </Link>
        )}
        <button
          onClick={logout}
          className="mt-2 flex items-center gap-2 rounded-xl px-4 py-3 text-base font-medium text-red-700 hover:bg-red-50"
        >
          <LogOut className="h-4 w-4" /> Sign out
        </button>
      </div>
    );
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((s) => !s)}
        className={cn(
          "inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors",
          transparent
            ? "bg-white/10 text-white hover:bg-white/20"
            : "bg-jade-50 text-ink-900 hover:bg-jade-100"
        )}
      >
        <Avatar user={user} />
        <span className="max-w-[140px] truncate">
          {user.full_name || user.email.split("@")[0]}
        </span>
        <ChevronDown className="h-3.5 w-3.5" />
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-border bg-white p-2 shadow-lift">
          <Link
            href="/account"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-ink-700 hover:bg-jade-50"
          >
            <UserIcon className="h-3.5 w-3.5" /> Profile
          </Link>
          <Link
            href="/account/history"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-ink-700 hover:bg-jade-50"
          >
            <History className="h-3.5 w-3.5" /> Chat history
          </Link>
          <Link
            href="/account/itineraries"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-ink-700 hover:bg-jade-50"
          >
            <Sparkles className="h-3.5 w-3.5" /> My itineraries
          </Link>
          {user.is_admin && (
            <Link
              href="/admin"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold text-jade-700 hover:bg-jade-50"
            >
              <Sparkles className="h-3.5 w-3.5" /> Admin
            </Link>
          )}
          <div className="my-1 h-px bg-border" />
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-red-700 hover:bg-red-50"
          >
            <LogOut className="h-3.5 w-3.5" /> Sign out
          </button>
        </div>
      )}
    </div>
  );
}

function Avatar({ user }: { user: { full_name?: string; email: string; avatar_url?: string } }) {
  if (user.avatar_url) {
    // eslint-disable-next-line @next/next/no-img-element
    return (
      <img
        src={user.avatar_url}
        alt=""
        className="h-6 w-6 rounded-full object-cover"
      />
    );
  }
  const initial = (user.full_name || user.email).slice(0, 1).toUpperCase();
  return (
    <span className="grid h-6 w-6 place-items-center rounded-full bg-saffron-300 text-[11px] font-bold text-jade-900">
      {initial}
    </span>
  );
}
