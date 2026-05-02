import Link from "next/link";
import { Camera, MapPin } from "lucide-react";

type District = {
  id: number;
  name: string;
  slug: string;
  province: string;
  description: string;
  attraction_count?: number;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const metadata = {
  title: "Photo gallery · LankaGuide",
  description:
    "Curated photography and video for all 25 districts of Sri Lanka.",
};

async function fetchDistricts(): Promise<District[]> {
  try {
    const res = await fetch(`${API}/api/v1/attractions/districts/`, {
      next: { revalidate: 600 },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return data?.results ?? data ?? [];
  } catch {
    return [];
  }
}

export default async function GalleryPage() {
  const districts = await fetchDistricts();

  return (
    <div className="container py-12 md:py-16">
      <header className="mb-12">
        <span className="kicker">
          <Camera className="h-3 w-3" />
          Gallery
        </span>
        <h1 className="display mt-3 text-4xl font-medium tracking-tightest text-ink-900 md:text-6xl">
          25 districts. <em className="text-jade-700 not-italic">One island.</em>
        </h1>
        <p className="mt-3 max-w-2xl text-base text-ink-600">
          Browse curated photography and video for every district of Sri Lanka,
          from the dry-zone north to the wet-zone south, the highland tea
          country to the eastern reefs.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {districts.map((d) => (
          <Link
            key={d.id}
            href={`/gallery/${d.slug || d.name.toLowerCase()}`}
            className="group relative overflow-hidden rounded-3xl border border-border bg-white shadow-soft transition-shadow hover:shadow-lift"
          >
            <div className="aspect-[4/3] w-full bg-gradient-to-br from-jade-700 via-jade-600 to-saffron-500">
              <div className="flex h-full flex-col justify-end p-5">
                <p className="kicker text-saffron-200 before:bg-saffron-200/60">
                  <MapPin className="h-3 w-3" /> {d.province}
                </p>
                <h2 className="display mt-2 text-2xl font-medium tracking-tightest text-white">
                  {d.name}
                </h2>
                <p className="mt-1 line-clamp-2 text-xs text-jade-50/80">
                  {d.description}
                </p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
