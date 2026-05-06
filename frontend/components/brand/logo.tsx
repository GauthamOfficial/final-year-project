import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * LankaGuide wordmark with a Sri Lanka-inspired island mark.
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
          <path
            d="M11 2.4c1.1.3 2.1 1.1 2.5 2.1.5 1.1.4 2.4 1 3.5.7 1.2 2 2 2.4 3.4.3 1-.1 1.9-.5 2.8-.4 1.1-.7 2.2-.6 3.4.1 1.1-.3 2.2-1.2 2.9-.8.7-1.9 1-2.9.9-1.1-.1-2.2.1-3.2.6-.9.4-1.9.6-2.9.3-1.2-.3-2.1-1.2-2.6-2.3-.5-1-.5-2.2-.2-3.3.3-1 .8-1.9 1.3-2.8.5-.8.8-1.8.8-2.8 0-1.1.3-2.1.9-2.9.6-.9 1.5-1.5 2.4-2 .8-.4 1.6-.8 2.2-1.8.5-.7 1.4-1.2 2.6-1Z"
            fill="currentColor"
            fillOpacity="0.14"
          />
          <path d="M11 2.4c1.1.3 2.1 1.1 2.5 2.1.5 1.1.4 2.4 1 3.5.7 1.2 2 2 2.4 3.4.3 1-.1 1.9-.5 2.8-.4 1.1-.7 2.2-.6 3.4.1 1.1-.3 2.2-1.2 2.9-.8.7-1.9 1-2.9.9-1.1-.1-2.2.1-3.2.6-.9.4-1.9.6-2.9.3-1.2-.3-2.1-1.2-2.6-2.3-.5-1-.5-2.2-.2-3.3.3-1 .8-1.9 1.3-2.8.5-.8.8-1.8.8-2.8 0-1.1.3-2.1.9-2.9.6-.9 1.5-1.5 2.4-2 .8-.4 1.6-.8 2.2-1.8.5-.7 1.4-1.2 2.6-1Z" />
          <path d="M11.5 8.5c-.9 2.1-1.3 4.2-1 6.4.2 1.2.6 2.4 1.2 3.5" />
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
      </span>
    </span>
  );

  if (!href) return inner;
  return <Link href={href} className="group">{inner}</Link>;
}
