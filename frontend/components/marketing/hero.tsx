import Link from "next/link";
import { ArrowRight, Compass, Play, Sparkles } from "lucide-react";
import { HERO_PHOTOS } from "@/lib/photos";

/**
 * Hero — full-bleed image with editorial typographic stack:
 *   • saffron kicker label
 *   • oversize Fraunces display headline with brushed-underline accent
 *   • lead paragraph
 *   • dual CTA (primary + secondary)
 *   • floating glass "trust" panel with stats / live activity
 */
export function Hero() {
  return (
    <section className="relative isolate min-h-[92vh] w-full overflow-hidden text-white">
      {/* Background photo */}
      <div className="absolute inset-0 -z-10">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={HERO_PHOTOS.sigiriya}
          alt="Sigiriya rock fortress at golden hour"
          className="h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-jade-900/85 via-jade-800/55 to-saffron-700/35" />
        <div className="absolute inset-0 bg-[radial-gradient(80%_60%_at_20%_30%,transparent,rgba(0,0,0,0.6))]" />
      </div>

      <div className="container relative flex min-h-[92vh] flex-col justify-end pb-24 pt-32 md:justify-center md:pb-32 md:pt-40">
        <div className="max-w-3xl reveal">
          <span className="kicker text-saffron-300 before:bg-saffron-300/60">
            <Sparkles className="h-3 w-3" />
            Travel companion · Pearl of the Indian Ocean
          </span>

          <h1 className="display mt-6 text-[clamp(2.75rem,7vw,5.75rem)] font-medium leading-[0.95] text-white">
            Wander Sri Lanka, <br className="hidden sm:block" />
            <span className="italic text-saffron-200">guided</span>{" "}
            <span className="underline-brush">by intelligence</span>
            <span className="text-saffron-300">.</span>
          </h1>

          <p className="mt-7 max-w-xl text-base leading-relaxed text-white/85 md:text-lg">
            Plan trips with a guide that actually knows the island,
            grounded in 25 districts of curated local knowledge, fluent in
            Sinhala &amp; Tamil, and honest when it doesn&apos;t know.
          </p>

          <div className="mt-10 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/itinerary"
              className="group inline-flex items-center justify-center gap-2 rounded-full bg-saffron-400 px-7 py-4 text-sm font-semibold text-jade-900 shadow-glow transition-all hover:bg-saffron-300"
            >
              Plan my trip
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/chat"
              className="group inline-flex items-center justify-center gap-2 rounded-full border border-white/30 bg-white/10 px-7 py-4 text-sm font-semibold text-white backdrop-blur transition-colors hover:bg-white/20"
            >
              <Compass className="h-4 w-4" />
              Ask anything about Sri Lanka
            </Link>
          </div>

          <div className="mt-12 flex items-center gap-6 text-xs text-white/70">
            <Link href="/signup" className="flex items-center gap-2 transition-colors hover:text-white">
              <span className="grid h-9 w-9 place-items-center rounded-full border border-white/30 bg-white/10 backdrop-blur">
                <Play className="h-3.5 w-3.5 fill-white" />
              </span>
              Create a free account
            </Link>
            <span className="hidden h-px w-12 bg-white/30 sm:block" />
            <span className="hidden sm:inline">English · Sinhala · Tamil · Voice + maps</span>
          </div>
        </div>

        {/* Floating glass info panel */}
        <div className="mt-16 grid gap-3 reveal reveal-3 md:absolute md:bottom-12 md:right-8 md:mt-0 md:w-[340px]">
          <div className="glass rounded-3xl p-5 shadow-lift">
            <div className="flex items-center justify-between">
              <span className="kicker text-saffron-600 before:bg-saffron-600/60">
                Live atlas
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-kicker text-jade-700">
                Live · 2026
              </span>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-4 text-jade-900">
              <div>
                <div className="display text-3xl font-semibold leading-none">
                  25
                </div>
                <div className="mt-1 text-[11px] uppercase tracking-kicker text-ink-600">
                  Districts
                </div>
              </div>
              <div>
                <div className="display text-3xl font-semibold leading-none">
                  250+
                </div>
                <div className="mt-1 text-[11px] uppercase tracking-kicker text-ink-600">
                  Attractions
                </div>
              </div>
              <div>
                <div className="display text-3xl font-semibold leading-none">
                  3
                </div>
                <div className="mt-1 text-[11px] uppercase tracking-kicker text-ink-600">
                  Languages
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
