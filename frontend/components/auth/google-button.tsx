"use client";

import { useEffect, useRef } from "react";

type GoogleCredentialResponse = { credential?: string };

type GoogleAccountsId = {
  initialize: (opts: {
    client_id: string;
    callback: (resp: GoogleCredentialResponse) => void;
  }) => void;
  renderButton: (
    el: HTMLElement,
    opts: Record<string, string | number | boolean>
  ) => void;
};

declare global {
  interface Window {
    google?: { accounts: { id: GoogleAccountsId } };
  }
}
const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID ?? "";

export function GoogleButton({
  onCredential,
  text = "signin_with",
}: {
  onCredential: (idToken: string) => void;
  text?: "signin_with" | "signup_with" | "continue_with";
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    const id = "google-identity-script";
    let s = document.getElementById(id) as HTMLScriptElement | null;
    if (!s) {
      s = document.createElement("script");
      s.id = id;
      s.src = "https://accounts.google.com/gsi/client";
      s.async = true;
      s.defer = true;
      document.body.appendChild(s);
    }
    const interval = setInterval(() => {
      if (!window.google || !ref.current) return;
      clearInterval(interval);
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (resp: GoogleCredentialResponse) => {
          if (resp?.credential) onCredential(resp.credential);
        },
      });
      window.google.accounts.id.renderButton(ref.current, {
        theme: "outline",
        size: "large",
        text,
        shape: "pill",
        width: 320,
      });
    }, 200);
    return () => clearInterval(interval);
  }, [onCredential, text]);

  if (!GOOGLE_CLIENT_ID) {
    return (
      <p className="text-center text-xs text-ink-500">
        Google sign-in is not configured.
      </p>
    );
  }
  return <div ref={ref} className="flex justify-center" />;
}
