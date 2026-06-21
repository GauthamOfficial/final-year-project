import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UserPreferences = {
  language: "en" | "si" | "ta";
  budgetRange?: string;
  interests: string[];
};

type State = {
  prefs: UserPreferences;
  setPrefs: (prefs: Partial<UserPreferences>) => void;
  reset: () => void;
};

const DEFAULTS: UserPreferences = {
  language: "en",
  interests: [],
};

/**
 * Global preferences store (PRD §5.1 onboarding capture). Persists to
 * localStorage so the next visit feels instantaneous; the backend mirror
 * lives in the `users` table.
 */
export const useUserStore = create<State>()(
  persist(
    (set) => ({
      prefs: DEFAULTS,
      setPrefs: (prefs) =>
        set((s) => ({ prefs: { ...s.prefs, ...prefs } })),
      reset: () => set({ prefs: DEFAULTS }),
    }),
    { name: "lankaguide.prefs" }
  )
);
