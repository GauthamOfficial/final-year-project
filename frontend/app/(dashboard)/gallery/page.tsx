import Link from "next/link";
import { Camera, MapPin } from "lucide-react";

type District = {
  id: number;
  name: string;
  slug: string;
  province: string;
  description: string;
  attraction_count?: number;
  hero_image_url?: string;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
/** Wikimedia fallbacks when no local district thumbnail exists. */
const DISTRICT_WIKIMEDIA_THUMBNAILS: Record<string, string> = {
  batticaloa:
    "https://commons.wikimedia.org/wiki/Special:FilePath/Sea_Fishing,_Batticaloa.jpg",
  kegalle:
    "https://commons.wikimedia.org/wiki/Special:FilePath/Kegalle_Town_Clock_Tower.jpg",
};

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

function mediaUrl(path?: string): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  if (path.startsWith("/")) return `${API}${path}`;
  return `${API}/${path}`;
}

async function fetchDistrictThumbnail(slug: string): Promise<string> {
  try {
    const res = await fetch(
      `${API}/api/v1/attractions/districts/${encodeURIComponent(slug)}/gallery/`,
      { next: { revalidate: 600 } }
    );
    if (!res.ok) return "";
    const data = await res.json();
    const firstMedia = Array.isArray(data?.media) ? data.media[0] : null;
    const raw = firstMedia?.cdn_url || firstMedia?.s3_key || "";
    return mediaUrl(raw);
  } catch {
    return "";
  }
}

export default async function GalleryPage() {
  const districts = await fetchDistricts();
  const districtsWithThumbs = await Promise.all(
    districts.map(async (district) => {
      if (district.hero_image_url) {
        return { ...district, hero_image_url: mediaUrl(district.hero_image_url) };
      }
      const galleryThumb = district.slug ? await fetchDistrictThumbnail(district.slug) : "";
      if (galleryThumb) {
        return { ...district, hero_image_url: galleryThumb };
      }
      const curatedThumb = district.slug
        ? (DISTRICT_WIKIMEDIA_THUMBNAILS[district.slug] ?? "")
        : "";
      return { ...district, hero_image_url: curatedThumb };
    })
  );

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
        {districtsWithThumbs.map((d) => (
          <Link
            key={d.id}
            href={`/gallery/${d.slug || d.name.toLowerCase()}`}
            className="group relative overflow-hidden rounded-3xl border border-border bg-white shadow-soft transition-shadow hover:shadow-lift"
          >
            <div className="relative aspect-[4/3] w-full bg-gradient-to-br from-jade-700 via-jade-600 to-saffron-500">
              {d.hero_image_url ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={mediaUrl(d.hero_image_url)}
                    alt={`${d.name} district`}
                    className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-black/20 to-black/10" />
                </>
              ) : null}
              <div className="relative z-10 flex h-full flex-col justify-end p-5">
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
