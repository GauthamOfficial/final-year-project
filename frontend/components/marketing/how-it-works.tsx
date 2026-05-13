import { MessageCircle, Map, ScanLine } from "lucide-react";

const STEPS = [
  {
    n: "01",
    icon: MessageCircle,
    title: "Ask the AI guide",
    body:
      "Type a question, like “best time for whale-watching in Mirissa?” or “what to pack for Horton Plains?”, and get a grounded, sourced answer with citations from a curated atlas.",
    accent: "jade",
  },
  {
    n: "02",
    icon: Map,
    title: "Build a real itinerary",
    body:
      "Tell us your dates, budget, group, and interests. The AI drafts a day-by-day plan you can swap, regenerate, or share by link, while respecting monsoons, crowd indexes, and travel time.",
    accent: "saffron",
  },
  {
    n: "03",
    icon: ScanLine,
    title: "Identify a landmark",
    body:
      "Upload or snap a photo of a stupa, fort, or coastline. Gemini Vision names the place, we match it to our attraction atlas, and the knowledge base adds a short, cited summary when available.",
    accent: "jade",
  },
] as const;

export function HowItWorks() {
  return (
    <section
      className="relative overflow-hidden border-y border-border/70 bg-jade-50/60 py-24 md:py-32"
      id="how"
    >
      {/* Decorative dotted column rule */}
      <div className="absolute inset-y-0 left-1/2 hidden w-px -translate-x-1/2 bg-[radial-gradient(circle,hsl(var(--border))_1px,transparent_1.5px)] bg-[length:1px_14px] md:block" />

      <div className="container relative">
        <div className="max-w-2xl">
          <span className="kicker">How it works</span>
          <h2 className="display mt-4 text-4xl font-medium tracking-tightest text-ink-900 md:text-6xl">
            Three tools.{" "}
            <em className="text-saffron-600 not-italic">One companion.</em>
          </h2>
          <p className="mt-5 text-base leading-relaxed text-ink-600">
            Built for the way travellers actually plan, with short questions on
            the train, deep planning sessions on the laptop, and curiosity
            in front of an unfamiliar temple.
          </p>
        </div>

        <div className="mt-16 grid gap-12 md:grid-cols-3">
          {STEPS.map((step, i) => {
            const accent =
              step.accent === "jade"
                ? "bg-jade-600 text-white"
                : "bg-saffron-400 text-jade-900";
            return (
              <div
                key={step.n}
                className="relative reveal"
                style={{ animationDelay: `${i * 80}ms` }}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`grid h-12 w-12 place-items-center rounded-2xl shadow-glow ${accent}`}
                  >
                    <step.icon className="h-5 w-5" />
                  </span>
                  <span className="display text-3xl font-medium text-ink-300">
                    {step.n}
                  </span>
                </div>
                <h3 className="display mt-6 text-2xl font-medium tracking-tightest text-ink-900 md:text-3xl">
                  {step.title}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-ink-600">
                  {step.body}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
