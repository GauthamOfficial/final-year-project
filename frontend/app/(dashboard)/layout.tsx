import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { AlertsBanner } from "@/components/alerts/AlertsBanner";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <div className="flex flex-1 flex-col pt-16 md:pt-20">
        <AlertsBanner />
        <main className="flex-1">{children}</main>
      </div>
      <SiteFooter />
    </div>
  );
}
