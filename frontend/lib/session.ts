/**
 * Legacy anonymous-session helpers were retired when JWT auth landed.
 * Use `lib/auth.ts` instead. These shims keep older imports compiling but
 * always return empty / no-op so the auth store remains the single source.
 */

export function getOrCreateSessionToken(): string {
  return "";
}

export function clearSessionToken() {
  // no-op
}
