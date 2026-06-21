import Link from "next/link";
import { SentimentBadge } from "@/components/attractions/SentimentBadge";
import { YouTubeFacade } from "@/components/gallery/youtube-facade";
import { notFound } from "next/navigation";
import { ArrowLeft, MapPin, Video } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type GalleryPayload = {
  district: {
    id: number;
    name: string;
    slug: string;
    province: string;
    description: string;
    climate_zone: string;
    youtube_video_ids: string[];
    hero_image_url?: string;
  };
  attractions: Array<{
    id: number;
    name: string;
    slug: string;
    category: string;
    sentiment_label: string | null;
    sentiment_score: number | null;
    positive_pct: number;
    sentiment_summary: string | null;
  }>;
  media: Array<{
    id: number;
    type: string;
    cdn_url: string;
    s3_key: string;
    caption: string;
    attribution: string;
    license: string;
    source_url: string;
    attraction_id: number | null;
  }>;
};

function mediaUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  if (path.startsWith("/")) return `${API}${path}`;
  return `${API}/${path}`;
}

async function fetchGallery(slug: string): Promise<GalleryPayload | null> {
  try {
    const res = await fetch(
      `${API}/api/v1/attractions/districts/${encodeURIComponent(slug)}/gallery/`,
      { next: { revalidate: 600 } }
    );
    if (!res.ok) return null;
    return (await res.json()) as GalleryPayload;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ district: string }>;
}) {
  const { district: districtSlug } = await params;
  const data = await fetchGallery(districtSlug);
  if (!data) return { title: "Gallery" };
  return {
    title: `${data.district.name} gallery · LankaGuide`,
    description: data.district.description.slice(0, 160),
  };
}

export default async function DistrictGalleryPage({
  params,
}: {
  params: Promise<{ district: string }>;
}) {
  const { district: districtSlug } = await params;
  const data = await fetchGallery(districtSlug);
  if (!data) notFound();

  const { district, attractions, media } = data;

  return (
    <div className="container py-12 md:py-16">
      <Link
        href="/gallery"
        className="mb-6 inline-flex items-center gap-2 text-xs font-semibold text-ink-500 hover:text-ink-900"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> All districts
      </Link>

      <header className="mb-10 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <span className="kicker">
            <MapPin className="h-3 w-3" /> {district.province} province
          </span>
          <h1 className="display mt-2 text-4xl font-medium tracking-tightest text-ink-900 md:text-6xl">
            {district.name}
          </h1>
          <p className="mt-3 max-w-2xl text-base text-ink-600">
            {district.description}
          </p>
        </div>
      </header>

      {media.length > 0 && (
        <section className="mb-14">
          <span className="kicker">Photography</span>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {media.map((m) => (
              <figure
                key={m.id}
                className="group overflow-hidden rounded-2xl border border-border bg-white shadow-soft"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={mediaUrl(m.cdn_url || m.s3_key)}
                  alt={m.caption || district.name}
                  className="aspect-[4/3] w-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                {(m.attribution || m.license) && (
                  <figcaption className="border-t border-border bg-bg-page/40 px-3 py-2 text-[10px] text-ink-500">
                    {m.attribution}
                    {m.license ? ` · ${m.license}` : ""}
                    {m.source_url ? (
                      <a
                        href={m.source_url}
                        className="ml-1 underline-offset-2 hover:underline"
                        target="_blank"
                        rel="noreferrer"
                      >
                        source
                      </a>
                    ) : null}
                  </figcaption>
                )}
              </figure>
            ))}
          </div>
        </section>
      )}

      {district.youtube_video_ids?.length > 0 && (
        <section className="mb-14">
          <span className="kicker">
            <Video className="h-3 w-3" /> On video
          </span>
          <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {district.youtube_video_ids.map((id) => (
              <YouTubeFacade
                key={id}
                id={id}
                title={`${district.name} travel video`}
              />
            ))}
          </div>
        </section>
      )}

      {attractions.length > 0 && (
        <section>
          <span className="kicker">In this district</span>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {attractions.map((a) => (
              <Link
                key={a.id}
                href={`/explore/${a.slug}`}
                className="group rounded-2xl border border-border bg-white px-5 py-4 shadow-soft transition-shadow hover:shadow-lift"
              >
                <p className="kicker">{a.category}</p>
                <p className="display mt-2 text-lg font-medium text-ink-900 group-hover:text-jade-700">
                  {a.name}
                </p>
                <div className="mt-3">
                  <SentimentBadge
                    label={
                      (a.sentiment_label as
                        | "positive"
                        | "neutral"
                        | "negative"
                        | null) ?? null
                    }
                    positive_pct={a.positive_pct ?? 0}
                    summary={a.sentiment_summary ?? ""}
                  />
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
