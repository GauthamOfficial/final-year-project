import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Tailwind class joiner — the standard `cn()` helper used by every shadcn/ui
 * primitive. Combines `clsx` (conditional / array support) with `tailwind-merge`
 * to dedupe conflicting utility classes (e.g. `px-2 px-4` → `px-4`).
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
