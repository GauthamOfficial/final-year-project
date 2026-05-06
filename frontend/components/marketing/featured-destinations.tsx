import Link from "next/link";
import { ArrowUpRight, MapPin } from "lucide-react";
import { FEATURED_DESTINATIONS, type FeaturedDestination } from "@/lib/photos";
import { cn } from "@/lib/utils";

/**
 * Bento-style featured destinations grid (CSS-grid asymmetry).
 *
 * Layout target (lg):
 *   ┌──────────────┬──────────┐
 *   │              │          │
 *   │   FEATURE    │   med    │
 *   │   (lg)       ├──────────┤
 *   │              │   med    │
 *   ├──────┬───────┴──────────┤
 *   │ sm   │  sm   │   sm     │
 *   └──────┴───────┴──────────┘
 */
export function FeaturedDestinations() {
  const lg = FEATURED_DESTINATIONS.find((d) => d.span === "lg")!;
  const md = FEATURED_DESTINATIONS.filter((d) => d.span === "md");
  const sm = FEATURED_DESTINATIONS.filter((d) => d.span === "sm");

  return (
    <section className="container py-24 md:py-32" id="stories">
      <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
        <div className="max-w-2xl">
          <span className="kicker">Where to begin</span>
          <h2 className="display mt-4 text-4xl font-medium tracking-tightest text-ink-900 md:text-6xl">
            Six places that <em className="text-jade-700 not-italic">define the island</em>.
          </h2>
          <p className="mt-5 max-w-lg text-base leading-relaxed text-ink-600">
            From rock-cut palaces and cloud-forest railways to leopard
            country and Dutch fort sunsets — start with the icons, then let
            the AI guide you off the beaten path.
          </p>
        </div>
        <Link
          href="/explore"
          className="group inline-flex items-center gap-2 self-start rounded-full border border-ink-900/15 bg-white px-5 py-3 text-sm font-semibold text-ink-900 shadow-soft transition-all hover:border-jade-300 hover:text-jade-700"
        >
          Browse all 60+ attractions
          <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
        </Link>
      </div>

      <div className="mt-12 grid grid-cols-1 gap-4 md:grid-cols-3 md:grid-rows-[420px_220px] lg:gap-6">
        {/* Hero card spanning 2 cols × 2 rows */}
        <DestinationCard
          dest={lg}
          className="md:col-span-2 md:row-span-2"
          tone="big"
        />
        {/* Two medium cards, stacked, last column row 1 + 2 */}
        {md.map((d, i) => (
          <DestinationCard key={d.slug} dest={d} className={cn(i === 0 && "md:row-start-1", i === 1 && "md:row-start-2")} />
        ))}
        {/* Three small cards across the bottom (new full-width row) */}
        {sm.map((d) => (
          <DestinationCard key={d.slug} dest={d} className="aspect-[4/3] md:h-auto md:min-h-[260px]" />
        ))}
      </div>
    </section>
  );
}

function DestinationCard({
  dest,
  className,
  tone = "default",
}: {
  dest: FeaturedDestination;
  className?: string;
  tone?: "default" | "big";
}) {
  return (
    <Link
      href={`/explore/${dest.slug}`}
      className={cn(
        "group relative isolate overflow-hidden rounded-3xl bg-jade-900 shadow-soft lift",
        className
      )}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={dest.photo}
        alt={dest.name}
        className="absolute inset-0 h-full w-full object-cover transition-transform duration-700 ease-out group-hover:scale-[1.06]"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-jade-900/95 via-jade-900/40 to-transparent" />

      {/* Top tag */}
      <div className="absolute left-5 top-5 z-10 flex items-center gap-2">
        <span className="rounded-full bg-white/15 px-3 py-1 text-[11px] font-semibold uppercase tracking-kicker text-white backdrop-blur">
          {dest.category}
        </span>
      </div>

      {/* Bottom content */}
      <div className="absolute inset-x-0 bottom-0 z-10 flex flex-col gap-2 p-5 text-white md:p-7">
        <span className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-kicker text-saffron-200">
          <MapPin className="h-3 w-3" />
          {dest.region}
        </span>
        <h3
          className={cn(
            "display font-medium tracking-tightest",
            tone === "big" ? "text-4xl md:text-5xl" : "text-2xl"
          )}
        >
          {dest.name}
        </h3>
        {tone === "big" && (
          <p className="mt-1 max-w-sm text-sm leading-relaxed text-white/85">
            {dest.blurb}
          </p>
        )}
        <div className="mt-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-kicker text-white/80 transition-colors group-hover:text-saffron-200">
          Explore
          <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
        </div>
      </div>
    </Link>
  );
}
