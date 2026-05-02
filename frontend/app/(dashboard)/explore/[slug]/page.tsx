/**
 * Dynamic attraction page (PRD §5.4 / §8.2).
 *
 * Fetches `GET /api/v1/attractions/{slug}/` server-side so SEO + first-paint
 * stay fast. Falls back to a friendly 404 if the slug isn't seeded.
 */
import { notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
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
};

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

export async function generateMetadata({ params }: { params: { slug: string } }) {
  const attraction = await fetchAttraction(params.slug);
  if (!attraction) return { title: "Not found · LankaGuide" };
  return {
    title: `${attraction.name} · LankaGuide`,
    description: attraction.description.slice(0, 160),
  };
}

export default async function AttractionPage({
  params,
}: {
  params: { slug: string };
}) {
  const attraction = await fetchAttraction(params.slug);
  if (!attraction) notFound();

  return (
    <div className="container py-8">
      <Link
        href="/explore"
        className={cn(
          buttonVariants({ variant: "ghost", size: "sm" }),
          "mb-4 inline-flex"
        )}
      >
        <ArrowLeft className="mr-1 h-4 w-4" />
        Back to explore
      </Link>

      <header className="mb-6 space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="amber">{attraction.category}</Badge>
          <span className="flex items-center gap-1 text-sm text-muted-foreground">
            <MapPin className="h-4 w-4" />
            {attraction.district.name} · {attraction.district.province}
          </span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight">
          {attraction.name}
        </h1>
        {attraction.address && (
          <p className="text-sm text-muted-foreground">{attraction.address}</p>
        )}
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_300px]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">About this place</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed">{attraction.description}</p>
              <div className="mt-6 rounded-md bg-muted/50 p-4 text-xs text-muted-foreground">
                <p className="mb-1 font-semibold uppercase tracking-wide">
                  About {attraction.district.name} District
                </p>
                <p>{attraction.district.description}</p>
                <p className="mt-1">
                  Climate zone:{" "}
                  <span className="font-medium">
                    {attraction.district.climate_zone}
                  </span>
                </p>
              </div>
            </CardContent>
          </Card>

          {attraction.media.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Gallery</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-3">
                {attraction.media.map((m) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    key={m.id}
                    src={m.cdn_url || m.s3_key}
                    alt={m.caption || attraction.name}
                    className="aspect-video w-full rounded-md object-cover"
                  />
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        <aside className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">At a glance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <Row label="Entry fee">
                {attraction.entry_fee_lkr
                  ? `LKR ${Number(attraction.entry_fee_lkr).toLocaleString()}`
                  : "Free / not listed"}
              </Row>
              <Row label="Trend score">
                {Math.round(Math.min(10, attraction.trend_score) * 10)}%
              </Row>
              <div className="space-y-1">
                <Row label="Crowd index">
                  {attraction.crowd_index}/10
                </Row>
                <Progress value={attraction.crowd_index * 10} />
              </div>
              {attraction.best_season.length > 0 && (
                <div>
                  <div className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
                    Best months
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {attraction.best_season.map((m) => (
                      <Badge key={m} variant="outline" className="text-[10px]">
                        {m}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              {attraction.lat && attraction.lng && (
                <Row label="Coordinates">
                  <a
                    className="text-primary underline"
                    href={`https://www.google.com/maps/search/?api=1&query=${attraction.lat},${attraction.lng}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {attraction.lat}, {attraction.lng}
                  </a>
                </Row>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Plan your visit</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <Link
                href={`/chat?seed=${encodeURIComponent(`Tell me more about ${attraction.name}`)}`}
                className={cn(buttonVariants(), "w-full")}
              >
                Ask the AI guide
              </Link>
              <Link
                href="/itinerary"
                className={cn(buttonVariants({ variant: "outline" }), "w-full")}
              >
                Add to my trip
              </Link>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <span className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <span className="font-medium">{children}</span>
    </div>
  );
}
