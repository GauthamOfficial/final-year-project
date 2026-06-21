import type { Metadata } from "next";
import { Fraunces, Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const sans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const display = Fraunces({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  style: ["normal", "italic"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "LankaGuide",
    template: "%s · LankaGuide",
  },
  description:
    "Plan smarter trips across the Pearl of the Indian Ocean. RAG-grounded answers, day-by-day itineraries, and a curated atlas of 25 Sri Lankan districts.",
  metadataBase: new URL("http://localhost:3000"),
  openGraph: {
    type: "website",
    title: "LankaGuide",
    description:
      "Plan smarter trips across the Pearl of the Indian Ocean, chat, build itineraries, and discover hidden gems.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${display.variable}`}>
      <body className="surface-sand min-h-screen font-sans text-ink-900 antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
