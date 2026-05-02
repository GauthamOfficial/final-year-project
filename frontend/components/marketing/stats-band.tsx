/**
 * Marquee stats band — single horizontal strip with editorial scale numbers.
 * Pure CSS marquee, no JS, accessibility-friendly (paused on hover).
 */
const ITEMS = [
  ["25", "districts curated"],
  ["60+", "attractions catalogued"],
  ["3", "languages: EN · සිංහල · தமிழ்"],
  ["6h", "trend cache (PRD §9.7)"],
  ["1.5s", "p50 chat response"],
  ["0", "ads, ever"],
];

export function StatsBand() {
  return (
    <section className="border-y border-border/70 bg-jade-900 text-jade-50">
      <div className="overflow-hidden py-6">
        <div className="flex w-max animate-marquee gap-12 [animation-play-state:running] hover:[animation-play-state:paused]">
          {[...ITEMS, ...ITEMS].map(([n, label], i) => (
            <div
              key={i}
              className="flex shrink-0 items-baseline gap-3 whitespace-nowrap"
            >
              <span className="display text-3xl font-medium leading-none text-saffron-300 md:text-4xl">
                {n}
              </span>
              <span className="text-xs font-medium uppercase tracking-kicker text-jade-100/70">
                {label}
              </span>
              <span className="display text-2xl text-jade-100/30">·</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
