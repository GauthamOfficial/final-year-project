/**
 * Itinerary builder page — wizard lands in Prompt 5B.
 */
import { ItineraryWizard } from "@/components/itinerary/wizard";

export const metadata = { title: "Build Trip · LankaGuide" };

export default function ItineraryPage() {
  return (
    <div className="container py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Build my Sri Lanka trip</h1>
        <p className="text-sm text-muted-foreground">
          Tell us a few preferences — we&apos;ll synthesise a day-by-day
          itinerary grounded in verified local knowledge.
        </p>
      </header>
      <ItineraryWizard />
    </div>
  );
}
