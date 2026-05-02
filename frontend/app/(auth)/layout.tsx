import { SiteHeader } from "@/components/layout/site-header";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteHeader />
      <main className="min-h-screen bg-gradient-to-b from-jade-50 via-white to-saffron-50/40 pt-24">
        {children}
      </main>
    </>
  );
}
