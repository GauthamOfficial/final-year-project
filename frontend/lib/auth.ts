"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type UserProfile = {
  id: number;
  email: string;
  full_name: string;
  avatar_url: string;
  role: "tourist" | "editor" | "admin";
  language: "en" | "si" | "ta";
  home_country: string;
  interests: string[];
  onboarding_complete: boolean;
  is_admin: boolean;
  created_at: string;
};

type AuthState = {
  access: string | null;
  refresh: string | null;
  user: UserProfile | null;
  hydrated: boolean;
  setSession: (s: { access: string; refresh: string; user: UserProfile }) => void;
  setUser: (user: UserProfile) => void;
  setAccess: (access: string) => void;
  clear: () => void;
  markHydrated: () => void;
};

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      access: null,
      refresh: null,
      user: null,
      hydrated: false,
      setSession: ({ access, refresh, user }) =>
        set({ access, refresh, user }),
      setUser: (user) => set({ user }),
      setAccess: (access) => set({ access }),
      clear: () => set({ access: null, refresh: null, user: null }),
      markHydrated: () => set({ hydrated: true }),
    }),
    {
      name: "lankaguide.auth",
      onRehydrateStorage: () => (state) => {
        state?.markHydrated();
      },
    }
  )
);

export function isAuthenticated() {
  if (typeof window === "undefined") return false;
  return !!useAuth.getState().access;
}

export function isAdmin() {
  if (typeof window === "undefined") return false;
  const u = useAuth.getState().user;
  return !!u && (u.is_admin || u.role === "admin");
}
