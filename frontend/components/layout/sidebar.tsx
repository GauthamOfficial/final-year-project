"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Compass,
  MapPinned,
  MessageSquare,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/chat", label: "AI Chat", icon: MessageSquare },
  { href: "/explore", label: "Explore", icon: Compass },
  { href: "/itinerary", label: "Build Trip", icon: MapPinned },
  { href: "/trends", label: "Trending", icon: TrendingUp },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-64 shrink-0 border-r bg-card lg:block">
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <Sparkles className="h-5 w-5 text-accent" />
        <span className="text-lg font-semibold tracking-tight">
          LankaGuide AI
        </span>
      </div>
      <nav className="flex flex-col gap-1 p-4">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active =
            pathname === href || pathname?.startsWith(`${href}/`);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent/10 hover:text-foreground",
                active && "bg-primary/10 text-primary"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-6 pt-4 text-xs text-muted-foreground">
        <p>Confidential — Academic Submission</p>
        <p>CS/2020/055 · 2025</p>
      </div>
    </aside>
  );
}

export function MobileTabBar() {
  const pathname = usePathname();
  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 flex h-14 items-center justify-around border-t bg-card lg:hidden">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active =
          pathname === href || pathname?.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-1 flex-col items-center justify-center gap-0.5 text-[11px] text-muted-foreground",
              active && "text-primary"
            )}
          >
            <Icon className="h-5 w-5" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
