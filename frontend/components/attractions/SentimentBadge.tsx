"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type SentimentLabel = "positive" | "neutral" | "negative" | null;

type SentimentBadgeProps = {
  label: SentimentLabel;
  positive_pct: number;
  summary: string;
};

export function SentimentBadge({
  label,
  positive_pct,
  summary,
}: SentimentBadgeProps) {
  if (label == null) {
    return null;
  }

  const badgeClass =
    label === "positive"
      ? "border-transparent bg-emerald-600 text-white hover:bg-emerald-600/90"
      : label === "negative"
        ? "border-transparent bg-red-600 text-white hover:bg-red-600/90"
        : "border-transparent bg-slate-500 text-white hover:bg-slate-500/90";

  const badgeText =
    label === "positive"
      ? `😊 ${positive_pct}% positive`
      : label === "neutral"
        ? "😐 Mixed reviews"
        : `😞 ${positive_pct}% positive`;

  return (
    <div className="flex flex-col gap-1.5">
      <Badge className={cn("w-fit font-semibold shadow-none", badgeClass)}>
        {badgeText}
      </Badge>
      {summary ? (
        <p className="sentiment-summary text-sm text-muted-foreground">
          {summary}
        </p>
      ) : null}
    </div>
  );
}
