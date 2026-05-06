import type { Metadata } from "next";
import { AdminGate } from "@/components/admin/admin-gate";
import { AdminSidebar } from "@/components/admin/admin-sidebar";

export const metadata: Metadata = {
  title: "Admin · LankaGuide",
  robots: { index: false, follow: false },
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminGate>
      <div className="flex min-h-screen flex-col bg-slate-950 text-slate-100 lg:flex-row">
        <AdminSidebar />
        <div className="flex-1 overflow-x-auto">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-8">{children}</div>
        </div>
      </div>
    </AdminGate>
  );
}
