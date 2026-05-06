"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Camera,
  FolderTree,
  LayoutDashboard,
  MapPin,
  MessageSquare,
  Shield,
  Sparkles,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/admin", label: "Overview", icon: LayoutDashboard, exact: true },
  { href: "/admin/users", label: "Users", icon: Users },
  { href: "/admin/districts", label: "Districts", icon: MapPin },
  { href: "/admin/attractions", label: "Attractions", icon: FolderTree },
  { href: "/admin/media", label: "Media", icon: Camera },
  { href: "/admin/knowledge", label: "Knowledge base", icon: Sparkles },
  { href: "/admin/chat", label: "Chat support", icon: MessageSquare },
  { href: "/admin/feedback", label: "Reviews & sentiment", icon: Shield },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="border-b border-slate-800 bg-slate-950 lg:flex lg:w-56 lg:shrink-0 lg:flex-col lg:border-b-0 lg:border-r lg:py-6">
      <Link
        href="/"
        className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-emerald-400/90 hover:text-emerald-300 lg:mb-8 lg:px-5 lg:py-0"
      >
        ← Back to app
      </Link>
      <nav className="flex gap-1 overflow-x-auto px-2 pb-3 lg:flex-1 lg:flex-col lg:gap-0.5 lg:overflow-visible lg:pb-0">
        {LINKS.map(({ href, label, icon: Icon, exact }) => {
          const active = exact
            ? pathname === href
            : pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-emerald-500/15 text-emerald-300"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-100"
              )}
            >
              <Icon className="h-4 w-4 shrink-0 opacity-80" />
              <span className="whitespace-nowrap">{label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="hidden px-5 pt-6 lg:mt-auto lg:block">
        <p className="flex items-center gap-2 text-[10px] font-medium uppercase tracking-wider text-slate-600">
          <BarChart3 className="h-3 w-3" /> Operator console
        </p>
      </div>
    </aside>
  );
}
