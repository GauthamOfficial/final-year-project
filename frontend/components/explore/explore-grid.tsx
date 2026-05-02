"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Filter, Loader2, MapPin, TrendingUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Select, SelectItem } from "@/components/ui/select";
import { api, toApiError } from "@/lib/api";

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
};

const CATEGORIES = [
  { id: "", label: "All categories" },
  { id: "beach", label: "Beach" },
  { id: "wildlife", label: "Wildlife" },
  { id: "cultural", label: "Cultural" },
  { id: "religious", label: "Religious" },
  { id: "adventure", label: "Adventure" },
  { id: "food", label: "Food" },
];

const CATEGORY_COLORS: Record<string, string> = {
  beach: "bg-blue-500/10 text-blue-700 border-blue-500/20",
  wildlife: "bg-emerald-500/10 text-emerald-700 border-emerald-500/20",
  cultural: "bg-amber-500/10 text-amber-700 border-amber-500/20",
  religious: "bg-violet-500/10 text-violet-700 border-violet-500/20",
  adventure: "bg-rose-500/10 text-rose-700 border-rose-500/20",
  food: "bg-orange-500/10 text-orange-700 border-orange-500/20",
};

// ─────────────────────────── Component ──────────────────────────────────
export function ExploreGrid() {
  const [districts, setDistricts] = useState<District[]>([]);
  const [attractions, setAttractions] = useState<Attraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [districtId, setDistrictId] = useState("");

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

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-3">
          <div className="sm:col-span-1">
            <Input
              placeholder="Search attractions…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Select value={category} onValueChange={setCategory}>
            {CATEGORIES.map((c) => (
              <SelectItem key={c.id || "all"} value={c.id}>
                {c.label}
              </SelectItem>
            ))}
          </Select>
          <Select value={districtId} onValueChange={setDistrictId}>
            <SelectItem value="">All districts</SelectItem>
            {districts.map((d) => (
              <SelectItem key={d.id} value={String(d.id)}>
                {d.name} ({d.province})
              </SelectItem>
            ))}
          </Select>
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-md border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-24 text-muted-foreground">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Loading attractions…
        </div>
      ) : attractions.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-24 text-center text-muted-foreground">
          <Filter className="h-8 w-8" />
          <p>No attractions match these filters.</p>
        </div>
      ) : (
        grouped.map(([districtName, list]) => (
          <section key={districtName} className="space-y-3">
            <header className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{districtName}</h2>
              <span className="text-xs text-muted-foreground">
                {list.length} attraction{list.length === 1 ? "" : "s"}
              </span>
            </header>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {list.map((a) => (
                <AttractionCard key={a.id} attraction={a} />
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}

// ─────────────────────────── Card ───────────────────────────────────────
function AttractionCard({ attraction }: { attraction: Attraction }) {
  const trendPct = Math.round(Math.min(10, attraction.trend_score) * 10);
  const colorClass =
    CATEGORY_COLORS[attraction.category] ??
    "bg-secondary text-secondary-foreground";

  return (
    <Link
      href={`/explore/${attraction.slug}`}
      className="group block focus:outline-none"
    >
      <Card className="h-full transition-shadow group-hover:shadow-md">
        <div className="aspect-[16/10] overflow-hidden rounded-t-lg bg-muted">
          {attraction.featured_media?.url ? (
            // Using <img> because the seeded URLs are external/CDN; switch to
            // next/image after configuring `images.remotePatterns`.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={attraction.featured_media.url}
              alt={attraction.featured_media.caption || attraction.name}
              className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <PlaceholderImage label={attraction.name} />
          )}
        </div>
        <CardContent className="space-y-3 p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="space-y-1">
              <h3 className="line-clamp-1 text-base font-semibold">
                {attraction.name}
              </h3>
              <p className="flex items-center gap-1 text-xs text-muted-foreground">
                <MapPin className="h-3 w-3" />
                {attraction.district_name}
              </p>
            </div>
            <Badge className={`shrink-0 border ${colorClass}`} variant="outline">
              {attraction.category}
            </Badge>
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                Crowd index
              </span>
              <span>{attraction.crowd_index}/10</span>
            </div>
            <Progress value={attraction.crowd_index * 10} />
          </div>
          {attraction.best_season.length > 0 && (
            <p className="text-[11px] text-muted-foreground">
              Best months: {attraction.best_season.slice(0, 4).join(", ")}
              {attraction.best_season.length > 4 && "…"}
            </p>
          )}
          <div className="flex items-center justify-between border-t pt-2">
            <span className="text-xs text-muted-foreground">Trend score</span>
            <Badge variant="amber">{trendPct}%</Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function PlaceholderImage({ label }: { label: string }) {
  // Deterministic pastel gradient so each attraction has a stable thumbnail.
  const hash = Array.from(label).reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const hue1 = hash % 360;
  const hue2 = (hue1 + 60) % 360;
  return (
    <div
      className="flex h-full w-full items-center justify-center text-2xl font-semibold text-white"
      style={{
        background: `linear-gradient(135deg, hsl(${hue1} 50% 40%), hsl(${hue2} 50% 55%))`,
      }}
      aria-label={label}
    >
      {label.charAt(0)}
    </div>
  );
}
