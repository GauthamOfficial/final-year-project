import { MobileTabBar, Sidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="relative flex-1 overflow-x-hidden pb-20 lg:pb-0">
        {children}
      </main>
      <MobileTabBar />
    </div>
  );
}
