"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowUpRight,
  Camera,
  Filter,
  MapPin,
  Search,
  SlidersHorizontal,
  Sparkles,
  X,
} from "lucide-react";
import { SentimentBadge } from "@/components/attractions/SentimentBadge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { LandmarkIdentifier } from "@/components/vision/LandmarkIdentifier";
import { api, toApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

// ─────────────────────────── Types ──────────────────────────────────────
type District = { id: number; name: string; province: string };
type Attraction = {
  id: number;
  name: string;
  slug: string;
  category: string;
  district: number;
  district_name: string;
  crowd_index: number;
  trend_score: number;
  best_season: number[];
  featured_media?: { type: string; url: string; caption: string } | null;
  sentiment_label?: string | null;
  sentiment_score?: number | null;
  positive_pct?: number;
  sentiment_summary?: string | null;
};

const CATEGORIES = [
  { id: "", label: "All" },
  { id: "cultural", label: "Cultural" },
  { id: "wildlife", label: "Wildlife" },
  { id: "beach", label: "Beach" },
  { id: "religious", label: "Religious" },
  { id: "adventure", label: "Adventure" },
  { id: "food", label: "Food" },
] as const;

const CATEGORY_TINTS: Record<string, string> = {
  cultural: "from-saffron-700/85 via-saffron-700/30 to-transparent",
  wildlife: "from-jade-800/85 via-jade-700/30 to-transparent",
  beach: "from-sky-900/85 via-sky-700/30 to-transparent",
  religious: "from-purple-900/85 via-purple-700/30 to-transparent",
  adventure: "from-rose-900/85 via-rose-700/30 to-transparent",
  food: "from-orange-900/85 via-orange-700/30 to-transparent",
};
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function mediaUrl(path?: string): string {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  if (path.startsWith("/")) return `${API_BASE}${path}`;
  return `${API_BASE}/${path}`;
}

// ─────────────────────────── Component ──────────────────────────────────
export function ExploreGrid() {
  const [districts, setDistricts] = useState<District[]>([]);
  const [attractions, setAttractions] = useState<Attraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("");
  const [districtId, setDistrictId] = useState<string>("");
  const [showFilters, setShowFilters] = useState(false);
  const [visionOpen, setVisionOpen] = useState(false);
  const [visionMountKey, setVisionMountKey] = useState(0);

  // Districts (one-shot)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data } = await api.get("/api/v1/attractions/districts/");
        if (!cancelled) setDistricts(data.results ?? data);
      } catch (err) {
        if (!cancelled) setError(toApiError(err).message);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  // Attractions (responsive to filters)
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (districtId) params.set("district_id", districtId);
    if (search) params.set("q", search);
    (async () => {
      try {
        const { data } = await api.get(
          `/api/v1/attractions/?${params.toString()}`
        );
        if (!cancelled) {
          setAttractions(data.results ?? data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) setError(toApiError(err).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [category, districtId, search]);

  const grouped = useMemo(() => {
    const map: Record<string, Attraction[]> = {};
    for (const a of attractions) {
      const key = a.district_name || "Unassigned";
      (map[key] ??= []).push(a);
    }
    return Object.entries(map).sort(([a], [b]) => a.localeCompare(b));
  }, [attractions]);

  const trending = useMemo(
    () => [...attractions].sort((a, b) => b.trend_score - a.trend_score).slice(0, 3),
    [attractions]
  );

  return (
    <>
      {/* ── Editorial header ── */}
      <section className="container pt-12 md:pt-20">
        <div className="grid gap-8 lg:grid-cols-[1.4fr_1fr] lg:items-end">
          <div className="reveal">
            <span className="kicker">
              <Sparkles className="h-3 w-3" />
              The atlas
            </span>
            <h1 className="display mt-4 text-4xl font-medium tracking-tightest text-ink-900 sm:text-5xl md:text-7xl">
              Every corner of the{" "}
              <em className="text-jade-700 not-italic">island</em>,
              <br />
              <span className="underline-brush">curated</span>.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-ink-600">
              {attractions.length || "60+"} attractions across{" "}
              {districts.length || "25"} districts, sortable by category,
              season, and crowd index. The data behind every itinerary.
            </p>
          </div>

          {/* Trending side card */}
          <div className="reveal reveal-2 rounded-3xl border border-border bg-white/80 p-5 shadow-soft backdrop-blur md:p-6">
            <div className="flex items-center justify-between">
              <span className="kicker">Trending now</span>
              <span className="text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
                Updated · 6h
              </span>
            </div>
            <div className="mt-4 space-y-3">
              {trending.length === 0 ? (
                <div className="h-20 animate-pulse rounded-xl bg-muted/60" />
              ) : (
                trending.map((a, i) => (
                  <Link
                    key={a.id}
                    href={`/explore/${a.slug}`}
                    className="group flex items-center gap-4 rounded-xl px-2 py-1 transition-colors hover:bg-jade-50/60"
                  >
                    <span className="display text-3xl font-medium text-ink-300 group-hover:text-jade-700">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-ink-900 group-hover:text-jade-700">
                        {a.name}
                      </p>
                      <p className="truncate text-[11px] uppercase tracking-kicker text-ink-500">
                        {a.district_name} · {a.category}
                      </p>
                    </div>
                    <ArrowUpRight className="h-3.5 w-3.5 text-ink-400 transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-jade-700" />
                  </Link>
                ))
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── Filter strip (sticky) ── */}
      <section className="sticky top-16 z-30 mt-12 border-y border-border/70 bg-background/85 backdrop-blur md:top-20">
        <div className="container flex flex-col gap-3 py-4 md:flex-row md:items-center md:justify-between">
          {/* Search */}
          <div className="relative flex-1 md:max-w-md">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search attractions, regions, themes…"
              className="h-11 w-full rounded-full border border-border bg-white pl-11 pr-14 text-sm text-ink-900 placeholder:text-ink-400 shadow-soft focus:border-jade-400 focus:outline-none focus:ring-2 focus:ring-jade-100"
            />
            <button
              type="button"
              onClick={() => {
                setVisionMountKey((k) => k + 1);
                setVisionOpen(true);
              }}
              aria-label="Identify landmark from photo"
              className="absolute right-3 top-1/2 grid h-9 w-9 shrink-0 -translate-y-1/2 place-items-center rounded-full border border-border bg-white text-ink-600 shadow-soft transition-colors hover:border-jade-300 hover:text-jade-700"
            >
              <Camera className="h-4 w-4" />
            </button>
          </div>

          {/* Category pills */}
          <div className="-mx-1 flex items-center gap-1 overflow-x-auto scrollbar-thin">
            {CATEGORIES.map((c) => {
              const active = category === c.id;
              return (
                <button
                  key={c.id || "all"}
                  onClick={() => setCategory(c.id)}
                  className={cn(
                    "inline-flex shrink-0 items-center gap-1.5 rounded-full border px-4 py-1.5 text-xs font-semibold transition-colors",
                    active
                      ? "border-jade-700 bg-jade-700 text-white shadow-soft"
                      : "border-border bg-white text-ink-700 hover:border-jade-300 hover:text-jade-700"
                  )}
                >
                  {c.label}
                </button>
              );
            })}
          </div>

          {/* District filter trigger */}
          <button
            onClick={() => setShowFilters((s) => !s)}
            className={cn(
              "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold shadow-soft transition-colors",
              districtId
                ? "border-jade-300 bg-jade-50 text-jade-700"
                : "border-border bg-white text-ink-700 hover:border-jade-300"
            )}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            District
            {districtId && (
              <span className="ml-1 rounded-full bg-jade-700 px-1.5 py-0.5 text-[10px] text-white">
                1
              </span>
            )}
          </button>
        </div>

        {showFilters && (
          <div className="border-t border-border/70 bg-white/90 backdrop-blur">
            <div className="container py-4">
              <div className="mb-2 flex items-center justify-between">
                <span className="kicker">Filter by district</span>
                {districtId && (
                  <button
                    onClick={() => setDistrictId("")}
                    className="inline-flex items-center gap-1 text-xs text-ink-600 hover:text-jade-700"
                  >
                    <X className="h-3 w-3" /> Clear
                  </button>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                {districts.map((d) => {
                  const active = districtId === String(d.id);
                  return (
                    <button
                      key={d.id}
                      onClick={() =>
                        setDistrictId(active ? "" : String(d.id))
                      }
                      className={cn(
                        "rounded-full border px-3 py-1.5 text-xs transition-colors",
                        active
                          ? "border-jade-600 bg-jade-600 text-white"
                          : "border-border bg-white text-ink-700 hover:border-jade-300"
                      )}
                    >
                      {d.name}
                      <span className="ml-1.5 text-[10px] opacity-60">
                        {d.province}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </section>

      {/* ── Body ── */}
      <section className="container py-12 md:py-16">
        {error && (
          <div className="mb-6 rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {error}
          </div>
        )}

        {loading ? (
          <SkeletonGrid />
        ) : attractions.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-16">
            {grouped.map(([districtName, list], idx) => (
              <DistrictSection
                key={districtName}
                name={districtName}
                attractions={list}
                index={idx}
              />
            ))}
          </div>
        )}
      </section>

      <Dialog open={visionOpen} onOpenChange={setVisionOpen}>
        <DialogContent className="max-h-[90vh] max-w-lg overflow-y-auto sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Identify a landmark from a photo</DialogTitle>
          </DialogHeader>
          <LandmarkIdentifier key={visionMountKey} />
        </DialogContent>
      </Dialog>
    </>
  );
}

// ─────────────────────────── Sub-components ─────────────────────────────
function DistrictSection({
  name,
  attractions,
  index,
}: {
  name: string;
  attractions: Attraction[];
  index: number;
}) {
  return (
    <section className="reveal" style={{ animationDelay: `${index * 60}ms` }}>
      <header className="mb-6 flex items-end justify-between gap-4 border-b border-border pb-4">
        <div>
          <span className="kicker">District</span>
          <h2 className="display mt-2 text-3xl font-medium tracking-tightest text-ink-900 md:text-4xl">
            {name}
          </h2>
        </div>
        <div className="text-right text-xs uppercase tracking-kicker text-ink-500">
          {attractions.length} place{attractions.length === 1 ? "" : "s"}
        </div>
      </header>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {attractions.map((a, i) => (
          <AttractionCard key={a.id} attraction={a} stagger={i} />
        ))}
      </div>
    </section>
  );
}

function AttractionCard({
  attraction,
  stagger,
}: {
  attraction: Attraction;
  stagger: number;
}) {
  const tint =
    CATEGORY_TINTS[attraction.category] ??
    "from-jade-900/85 via-jade-700/30 to-transparent";
  const trendPct = Math.round(Math.min(10, attraction.trend_score) * 10);
  const featuredUrl = mediaUrl(attraction.featured_media?.url);
  const imageUrl = featuredUrl || "";

  return (
    <Link
      href={`/explore/${attraction.slug}`}
      className="group relative isolate flex aspect-[4/5] flex-col justify-end overflow-hidden rounded-3xl bg-jade-900 shadow-soft lift reveal"
      style={{ animationDelay: `${stagger * 40}ms` }}
    >
      {imageUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={imageUrl}
          alt={attraction.featured_media?.caption || attraction.name}
          className="absolute inset-0 -z-10 h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-110"
        />
      ) : (
        <PlaceholderCanvas label={attraction.name} />
      )}

      <div
        className={cn(
          "absolute inset-0 -z-10 bg-gradient-to-t",
          tint
        )}
      />

      {/* Top tag */}
      <div className="absolute left-4 top-4 z-10 flex items-center gap-1.5">
        <span className="rounded-full bg-white/15 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-kicker text-white backdrop-blur">
          {attraction.category}
        </span>
        {trendPct > 70 && (
          <span className="rounded-full bg-saffron-400 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-kicker text-jade-900">
            Trending
          </span>
        )}
      </div>

      {/* Bottom content */}
      <div className="relative z-10 space-y-2 p-5 text-white">
        <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-kicker text-saffron-200">
          <MapPin className="h-3 w-3" />
          {attraction.district_name}
        </span>
        <h3 className="display text-2xl font-medium leading-tight tracking-tightest">
          {attraction.name}
        </h3>
        <div className="[&_p.sentiment-summary]:text-white/80">
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
        <div className="flex items-center justify-between pt-2">
          <CrowdMeter value={attraction.crowd_index} />
          <ArrowUpRight className="h-4 w-4 text-white/80 transition-all group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-saffron-200" />
        </div>
      </div>
    </Link>
  );
}

function CrowdMeter({ value }: { value: number }) {
  const segments = 10;
  return (
    <div className="flex flex-col gap-0.5 text-[10px] uppercase tracking-kicker text-white/70">
      <span>Crowd · {value}/10</span>
      <div className="flex gap-0.5">
        {Array.from({ length: segments }).map((_, i) => (
          <span
            key={i}
            className={cn(
              "h-1 w-2 rounded-full",
              i < value ? "bg-saffron-300" : "bg-white/25"
            )}
          />
        ))}
      </div>
    </div>
  );
}

function PlaceholderCanvas({ label }: { label: string }) {
  const hash = Array.from(label).reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const hue = hash % 360;
  return (
    <div
      className="absolute inset-0 -z-10"
      style={{
        background: `linear-gradient(135deg, hsl(${hue} 35% 22%) 0%, hsl(${
          (hue + 50) % 360
        } 45% 35%) 100%)`,
      }}
      aria-label={label}
    />
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-24 text-center text-ink-600">
      <Filter className="h-8 w-8 text-ink-400" />
      <p className="display text-2xl font-medium text-ink-900">
        No matches yet.
      </p>
      <p className="max-w-md text-sm">
        Try clearing a filter, broadening the category, or asking the AI
        guide instead.
      </p>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="aspect-[4/5] animate-pulse rounded-3xl bg-muted/60"
          style={{ animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  );
}
