/**
 * Destination Explorer — UI lands in Prompt 5C.
 */
import { ExploreGrid } from "@/components/explore/explore-grid";

export const metadata = { title: "Explore · LankaGuide" };

export default function ExplorePage() {
  return (
    <div className="container py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Explore Sri Lanka</h1>
        <p className="text-sm text-muted-foreground">
          Browse 25 districts and curated attractions, filtered by category and
          season.
        </p>
      </header>
      <ExploreGrid />
    </div>
  );
}
