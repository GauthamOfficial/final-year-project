/** English relative time for ISO timestamps (no extra deps). */
export function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  let diffSec = Math.round((then - Date.now()) / 1000);
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  const abs = Math.abs(diffSec);
  if (abs < 60) return rtf.format(diffSec, "second");
  diffSec = Math.round(diffSec / 60);
  if (Math.abs(diffSec) < 60) return rtf.format(diffSec, "minute");
  diffSec = Math.round(diffSec / 60);
  if (Math.abs(diffSec) < 24) return rtf.format(diffSec, "hour");
  diffSec = Math.round(diffSec / 24);
  if (Math.abs(diffSec) < 7) return rtf.format(diffSec, "day");
  diffSec = Math.round(diffSec / 7);
  if (Math.abs(diffSec) < 5) return rtf.format(diffSec, "week");
  diffSec = Math.round(diffSec / 4.345);
  if (Math.abs(diffSec) < 12) return rtf.format(diffSec, "month");
  diffSec = Math.round(diffSec / 12);
  return rtf.format(diffSec, "year");
}
