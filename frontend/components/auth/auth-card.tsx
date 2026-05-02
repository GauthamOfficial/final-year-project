import Link from "next/link";
import { Sparkles } from "lucide-react";

export function AuthCard({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <div className="container max-w-md py-12">
      <Link
        href="/"
        className="kicker mb-6 inline-flex text-jade-700 before:bg-jade-700/60"
      >
        <Sparkles className="h-3 w-3" /> LankaGuide
      </Link>
      <div className="rounded-3xl border border-border bg-white p-8 shadow-lift md:p-10">
        <h1 className="display text-3xl font-medium tracking-tightest text-ink-900">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-2 text-sm leading-relaxed text-ink-600">
            {subtitle}
          </p>
        )}
        <div className="mt-8 space-y-5">{children}</div>
        {footer && (
          <div className="mt-6 border-t border-border pt-6 text-sm text-ink-600">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
