import Link from "next/link";
import { AttractionSeasonalPanel } from "@/components/attractions/AttractionSeasonalPanel";
import { SentimentBadge } from "@/components/attractions/SentimentBadge";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  Calendar,
  Compass,
  MapPin,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import { MapView } from "@/components/maps/map-view";
import { WeatherCard } from "@/components/weather/weather-card";
import { resolveLocalAttractionImage } from "@/lib/local-attraction-images";
import { cn } from "@/lib/utils";

type AttractionDetail = {
  id: number;
  name: string;
  slug: string;
  category: string;
  description: string;
  address: string;
  lat: string | null;
  lng: string | null;
  entry_fee_lkr: string | null;
  best_season: number[];
  crowd_index: number;
  trend_score: number;
  best_months_names?: string[];
  district: {
    id: number;
    name: string;
    province: string;
    description: string;
    climate_zone: string;
  };
  media: Array<{
    id: number;
    type: string;
    cdn_url: string;
    s3_key: string;
    caption: string;
  }>;
  created_at: string;
  sentiment_label: string | null;
  sentiment_score: number | null;
  positive_pct: number;
  sentiment_summary: string | null;
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function mediaUrl(path: string): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  if (path.startsWith("/")) return `${API}${path}`;
  return `${API}/${path}`;
}

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

async function fetchAttraction(slug: string): Promise<AttractionDetail | null> {
  try {
    const res = await fetch(`${API}/api/v1/attractions/${slug}/`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) return null;
    return (await res.json()) as AttractionDetail;
  } catch {
    return null;
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const attraction = await fetchAttraction(slug);
  if (!attraction) return { title: "Not found" };
  return {
    title: attraction.name,
    description: attraction.description.slice(0, 160),
  };
}

export default async function AttractionPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const attraction = await fetchAttraction(slug);
  if (!attraction) notFound();

  const localHero = resolveLocalAttractionImage({ slug: attraction.slug });
  const apiHero = attraction.media[0]
    ? mediaUrl(attraction.media[0].cdn_url || attraction.media[0].s3_key)
    : null;
  const heroImage = localHero || apiHero || null;
  const trendPct = Math.round(Math.min(10, attraction.trend_score) * 10);

  return (
    <article>
      {/* ── Editorial hero ── */}
      <section className="relative isolate w-full overflow-hidden text-white">
        <div className="absolute inset-0 -z-10">
          {heroImage ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={heroImage}
              alt={attraction.name}
              className="h-full w-full object-cover"
            />
          ) : (
            <div className="h-full w-full bg-gradient-to-br from-jade-900 via-jade-700 to-saffron-700" />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-jade-900/95 via-jade-900/55 to-jade-900/30" />
        </div>

        <div className="container flex min-h-[80vh] flex-col justify-end pb-16 pt-32 md:pb-24 md:pt-40">
          <Link
            href="/explore"
            className="mb-8 inline-flex w-max items-center gap-2 rounded-full border border-white/30 bg-white/10 px-4 py-1.5 text-xs font-medium text-white backdrop-blur transition-colors hover:bg-white/20"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to atlas
          </Link>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full bg-saffron-400 px-3 py-1 font-semibold uppercase tracking-kicker text-jade-900">
              {attraction.category}
            </span>
            <span className="flex items-center gap-1.5 text-saffron-200">
              <MapPin className="h-3.5 w-3.5" />
              {attraction.district.name} · {attraction.district.province}
            </span>
          </div>

          <h1 className="display mt-6 max-w-4xl text-[clamp(2.25rem,8vw,6rem)] font-medium leading-[0.95] tracking-tightest text-white">
            {attraction.name}
          </h1>

          <div className="mt-4 max-w-2xl [&_p.sentiment-summary]:text-white/85">
            <SentimentBadge
              label={
                (attraction.sentiment_label as
                  | "positive"
                  | "neutral"
                  | "negative"
                  | null) ?? null
              }
              positive_pct={attraction.positive_pct ?? 0}
              summary={attraction.sentiment_summary ?? ""}
            />
          </div>

          {attraction.address && (
            <p className="mt-4 max-w-xl text-sm text-white/75">
              {attraction.address}
            </p>
          )}
        </div>
      </section>

      {/* ── Body ── */}
      <section className="relative z-10 container -mt-16 grid gap-10 pb-24 lg:grid-cols-[1fr_320px]">
        {/* Main column */}
        <div className="space-y-10">
          <div className="rounded-3xl border border-border bg-white p-8 shadow-lift md:p-12">
            <span className="kicker">About this place</span>
            <p className="display mt-4 text-2xl font-medium leading-snug text-ink-900 md:text-3xl">
              {attraction.description.split(". ")[0]}.
            </p>
            <p className="mt-6 whitespace-pre-line text-base leading-relaxed text-ink-700">
              {attraction.description.split(". ").slice(1).join(". ")}
            </p>
          </div>

          <AttractionSeasonalPanel slug={attraction.slug} />

          <div className="rounded-3xl border border-jade-100 bg-jade-50/60 p-8 md:p-10">
            <span className="kicker">About the district</span>
            <h2 className="display mt-3 text-3xl font-medium tracking-tightest text-ink-900">
              {attraction.district.name}
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-ink-700">
              {attraction.district.description}
            </p>
            <div className="mt-6 flex flex-wrap gap-3 text-xs">
              <span className="chip">
                Climate · {attraction.district.climate_zone}
              </span>
              <span className="chip">Province · {attraction.district.province}</span>
            </div>
          </div>

          {attraction.media.length > 1 && (
            <div className="space-y-4">
              <span className="kicker">Gallery</span>
              <div className="grid gap-3 sm:grid-cols-2">
                {attraction.media.map((m, i) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    key={m.id}
                    src={mediaUrl(m.cdn_url || m.s3_key)}
                    alt={m.caption || attraction.name}
                    className={cn(
                      "aspect-[4/3] w-full rounded-2xl object-cover shadow-soft",
                      i === 0 && "sm:col-span-2 sm:aspect-[16/8]"
                    )}
                  />
                ))}
              </div>
            </div>
          )}

          {attraction.lat && attraction.lng && (
            <div className="space-y-4">
              <span className="kicker">On the map</span>
              <MapView
                stops={[
                  {
                    id: attraction.id,
                    name: attraction.name,
                    lat: Number(attraction.lat),
                    lng: Number(attraction.lng),
                  },
                ]}
                height={320}
                zoom={11}
                showLine={false}
              />
            </div>
          )}
        </div>

        {/* Side rail */}
        <aside className="space-y-4 lg:sticky lg:top-28 lg:self-start">
          <WeatherCard districtId={attraction.district.id} />
          <div className="rounded-3xl border border-border bg-white p-6 shadow-soft">
            <span className="kicker">At a glance</span>
            <dl className="mt-5 space-y-4 text-sm">
              <Stat label="Entry fee">
                {attraction.entry_fee_lkr
                  ? `LKR ${Number(attraction.entry_fee_lkr).toLocaleString()}`
                  : "Free / not listed"}
              </Stat>
              <Stat label="Trend score">
                <span className="inline-flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5 text-saffron-600" />
                  {trendPct}% momentum
                </span>
              </Stat>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
                  Crowd index · {attraction.crowd_index}/10
                </p>
                <div className="mt-2 flex gap-1">
                  {Array.from({ length: 10 }).map((_, i) => (
                    <span
                      key={i}
                      className={cn(
                        "h-1.5 flex-1 rounded-full",
                        i < attraction.crowd_index
                          ? "bg-jade-600"
                          : "bg-muted"
                      )}
                    />
                  ))}
                </div>
              </div>
              {attraction.best_season.length > 0 && (
                <div>
                  <p className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
                    <Calendar className="h-3 w-3" /> Best months
                  </p>
                  <div className="mt-2 grid grid-cols-6 gap-1">
                    {MONTHS.map((m, i) => {
                      const idx = i + 1;
                      const isBest = attraction.best_season.includes(idx);
                      return (
                        <span
                          key={m}
                          className={cn(
                            "rounded-md px-1 py-1 text-center text-[10px] font-semibold uppercase tracking-tight",
                            isBest
                              ? "bg-jade-600 text-white"
                              : "bg-muted text-ink-400"
                          )}
                        >
                          {m[0]}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
              {attraction.lat && attraction.lng && (
                <Stat label="Location">
                  <a
                    className="text-jade-700 underline-offset-4 hover:underline"
                    href={`https://www.google.com/maps/search/?api=1&query=${attraction.lat},${attraction.lng}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open in Maps
                  </a>
                </Stat>
              )}
            </dl>
          </div>

          <div className="rounded-3xl border border-jade-700 bg-jade-900 p-6 text-jade-50 shadow-glow">
            <span className="kicker text-saffron-300 before:bg-saffron-300/60">
              <Sparkles className="h-3 w-3" />
              Plan with this place
            </span>
            <h3 className="display mt-3 text-xl font-medium leading-tight text-white">
              Add to a custom itinerary or ask the AI for tips.
            </h3>
            <div className="mt-4 flex flex-col gap-2">
              <Link
                href="/itinerary"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-saffron-400 px-5 py-2.5 text-sm font-semibold text-jade-900 transition-colors hover:bg-saffron-300"
              >
                <Compass className="h-4 w-4" />
                Build an itinerary
              </Link>
              <Link
                href={`/chat?seed=${encodeURIComponent(
                  `Tell me more about ${attraction.name}`
                )}`}
                className="inline-flex items-center justify-center gap-2 rounded-full border border-white/20 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white backdrop-blur transition-colors hover:bg-white/20"
              >
                Ask the AI guide
              </Link>
            </div>
          </div>
        </aside>
      </section>
    </article>
  );
}

function Stat({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-semibold text-ink-900">{children}</dd>
    </div>
  );
}
