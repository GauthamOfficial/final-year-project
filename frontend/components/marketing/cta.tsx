import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import { HERO_PHOTOS } from "@/lib/photos";

export function ClosingCta() {
  return (
    <section className="container py-24 md:py-32">
      <div className="relative isolate overflow-hidden rounded-[2.5rem] bg-jade-900 p-10 text-white shadow-lift md:p-20">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={HERO_PHOTOS.teaEstate}
          alt="Tea estate, central highlands"
          className="absolute inset-0 -z-10 h-full w-full object-cover opacity-40"
        />
        <div className="absolute inset-0 -z-10 bg-gradient-to-br from-jade-900/95 via-jade-800/85 to-saffron-700/40" />

        <div className="grid gap-12 md:grid-cols-[1.5fr_1fr] md:items-end">
          <div>
            <span className="kicker text-saffron-300 before:bg-saffron-300/60">
              <Sparkles className="h-3 w-3" />
              Open · free · no signup
            </span>
            <h2 className="display mt-5 text-4xl font-medium tracking-tightest text-white md:text-6xl">
              Plan a trip you&apos;ll <em className="text-saffron-200 not-italic">remember</em> —
              not just one you booked.
            </h2>
            <p className="mt-5 max-w-lg text-base leading-relaxed text-white/80">
              An anonymous session is enough to save your itinerary, share
              it with a partner, and revisit it from any device.
            </p>
          </div>
          <div className="flex flex-col gap-3 md:items-end">
            <Link
              href="/itinerary"
              className="group inline-flex items-center gap-2 rounded-full bg-saffron-400 px-7 py-4 text-sm font-semibold text-jade-900 shadow-glow transition-all hover:bg-saffron-300"
            >
              Start your itinerary
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/chat"
              className="text-sm font-medium text-white/85 underline-offset-4 hover:text-saffron-200 hover:underline"
            >
              Or chat first →
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
