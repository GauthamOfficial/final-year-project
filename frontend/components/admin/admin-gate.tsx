"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";

export function AdminGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, hydrated } = useAuth();

  useEffect(() => {
    if (!hydrated) return;
    const loginUrl = `/login?next=${encodeURIComponent(pathname)}&admin=1`;
    if (!user) {
      router.replace(loginUrl);
      return;
    }
    if (!user.is_admin && user.role !== "admin") {
      router.replace(loginUrl);
    }
  }, [hydrated, user, pathname, router]);

  if (!hydrated || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-200">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
      </div>
    );
  }

  if (!user.is_admin && user.role !== "admin") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-200">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
      </div>
    );
  }

  return <>{children}</>;
}
