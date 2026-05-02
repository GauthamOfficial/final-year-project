"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, Sparkles, X } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/explore", label: "Explore" },
  { href: "/itinerary", label: "Plan a trip" },
  { href: "/chat", label: "Ask the guide" },
  { href: "/#stories", label: "Stories" },
];

export function SiteHeader({ transparentTop = false }: { transparentTop?: boolean }) {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(!transparentTop);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!transparentTop) return;
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [transparentTop]);

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

        <nav className="hidden items-center gap-1 md:flex">
          {NAV.map((item) => {
            const active = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative rounded-full px-4 py-2 text-sm font-medium transition-colors",
                  transparent
                    ? "text-white/85 hover:text-white"
                    : "text-ink-700 hover:text-ink-900",
                  active && (transparent ? "text-white" : "text-jade-700")
                )}
              >
                {item.label}
                {active && (
                  <span
                    className={cn(
                      "absolute inset-x-4 -bottom-0.5 h-0.5 rounded-full",
                      transparent ? "bg-saffron-400" : "bg-jade-600"
                    )}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Link
            href="/chat"
            className={cn(
              "group inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold shadow-soft transition-all",
              transparent
                ? "bg-white text-jade-700 hover:bg-saffron-50"
                : "bg-jade-600 text-white hover:bg-jade-700 hover:shadow-lift"
            )}
          >
            <Sparkles className="h-4 w-4" />
            Start exploring
          </Link>
        </div>

        <button
          aria-label="Open menu"
          onClick={() => setOpen((o) => !o)}
          className={cn(
            "inline-flex h-10 w-10 items-center justify-center rounded-full border md:hidden",
            transparent
              ? "border-white/30 text-white"
              : "border-border bg-white text-ink-900"
          )}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div className="md:hidden">
          <div className="border-t border-border bg-background/95 backdrop-blur">
            <div className="container flex flex-col gap-1 py-4">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className="rounded-xl px-4 py-3 text-base font-medium text-ink-900 hover:bg-muted"
                >
                  {item.label}
                </Link>
              ))}
              <Link
                href="/chat"
                onClick={() => setOpen(false)}
                className="mt-2 flex items-center justify-center gap-2 rounded-full bg-jade-600 px-4 py-3 text-sm font-semibold text-white"
              >
                <Sparkles className="h-4 w-4" />
                Start exploring
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
