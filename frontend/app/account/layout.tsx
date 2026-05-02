"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Compass, History, Settings, User as UserIcon } from "lucide-react";
import { SiteHeader } from "@/components/layout/site-header";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/account", label: "Profile", icon: UserIcon },
  { href: "/account/history", label: "Chat history", icon: History },
  { href: "/account/itineraries", label: "My itineraries", icon: Compass },
  { href: "/account/settings", label: "Settings", icon: Settings },
];

export default function AccountLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, hydrated } = useAuth();

  useEffect(() => {
    if (hydrated && !user) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [hydrated, user, router, pathname]);

  if (!hydrated || !user) {
    return (
      <>
        <SiteHeader />
        <main className="container min-h-screen pt-32 text-sm text-ink-500">
          Loading your account…
        </main>
      </>
    );
  }

  return (
    <>
      <SiteHeader />
      <main className="container grid min-h-screen gap-10 pb-20 pt-28 md:grid-cols-[240px_1fr]">
        <aside className="space-y-1">
          <div className="rounded-2xl border border-border bg-white p-4 shadow-soft">
            <p className="text-xs font-semibold uppercase tracking-kicker text-ink-500">
              Signed in as
            </p>
            <p className="mt-1 truncate text-sm font-semibold text-ink-900">
              {user.full_name || user.email}
            </p>
            <p className="text-xs text-ink-500">{user.email}</p>
          </div>
          <nav className="mt-3 flex flex-col gap-0.5">
            {NAV.map((it) => {
              const active = pathname === it.href;
              const Icon = it.icon;
              return (
                <Link
                  key={it.href}
                  href={it.href}
                  className={cn(
                    "flex items-center gap-2 rounded-xl px-3 py-2 text-sm transition-colors",
                    active
                      ? "bg-jade-700 text-white"
                      : "text-ink-700 hover:bg-jade-50"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  {it.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <section>{children}</section>
      </main>
    </>
  );
}
