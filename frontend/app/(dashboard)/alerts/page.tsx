import type { Metadata } from "next";
import { AlertsPageContent } from "./alerts-page-content";

export const metadata: Metadata = {
  title: "Travel advisories · LankaGuide",
  description:
    "Stay informed about current conditions and travel advisories across Sri Lanka.",
};

export default function AlertsPage() {
  return (
    <div className="min-h-[50vh]">
      <div className="container max-w-3xl border-b border-border/60 pb-8 pt-10 md:pt-14">
        <h1 className="font-display text-3xl font-medium tracking-tight text-ink-900 md:text-4xl">
          Travel Advisories &amp; Weather Alerts
        </h1>
        <p className="mt-3 max-w-2xl text-base text-ink-600">
          Stay informed about current conditions across Sri Lanka
        </p>
      </div>
      <AlertsPageContent />
    </div>
  );
}
