import { ItineraryWizard } from "@/components/itinerary/wizard";

export const metadata = {
  title: "Plan a trip",
  description:
    "Build a day-by-day Sri Lanka itinerary in five quick decisions. Swap, regenerate, share.",
};

export default function ItineraryPage() {
  return <ItineraryWizard />;
}
