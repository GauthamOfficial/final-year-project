import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * LankaGuide wordmark — a stylised SVG mark (jade leaf + saffron sun)
 * paired with a Fraunces wordmark. Use everywhere the brand appears.
 */
export function Logo({
  href = "/",
  className,
  invert = false,
}: {
  href?: string | null;
  className?: string;
  invert?: boolean;
}) {
  const inner = (
    <span className={cn("flex items-center gap-2.5", className)}>
      <span
        className={cn(
          "relative grid h-9 w-9 place-items-center rounded-2xl border shadow-soft",
          invert
            ? "border-white/20 bg-white/10 text-white"
            : "border-jade-100 bg-white text-jade-700"
        )}
      >
        <svg
          viewBox="0 0 24 24"
          aria-hidden
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 2C7 6 5 10 5 13a7 7 0 0 0 14 0c0-3-2-7-7-11Z" fill="currentColor" fillOpacity="0.12" />
          <path d="M12 2C7 6 5 10 5 13a7 7 0 0 0 14 0c0-3-2-7-7-11Z" />
          <path d="M12 22V11" />
        </svg>
        <span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-saffron-400 ring-2 ring-white" />
      </span>
      <span className="flex flex-col leading-none">
        <span
          className={cn(
            "display text-[1.2rem] font-medium tracking-tightest",
            invert ? "text-white" : "text-ink-900"
          )}
        >
          LankaGuide
        </span>
        <span
          className={cn(
            "mt-0.5 text-[10px] font-semibold uppercase tracking-kicker",
            invert ? "text-saffron-300" : "text-saffron-600"
          )}
        >
          AI · Sri Lanka
        </span>
      </span>
    </span>
  );

  if (!href) return inner;
  return <Link href={href} className="group">{inner}</Link>;
}
