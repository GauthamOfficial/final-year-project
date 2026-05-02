import Link from "next/link";
import { Logo } from "@/components/brand/logo";
import { ExternalLink, Mail, MapPin } from "lucide-react";

const COLUMNS = [
  {
    title: "Discover",
    links: [
      { href: "/explore", label: "All destinations" },
      { href: "/explore?category=cultural", label: "Cultural sites" },
      { href: "/explore?category=wildlife", label: "Wildlife parks" },
      { href: "/explore?category=beach", label: "Beaches & coast" },
    ],
  },
  {
    title: "Plan",
    links: [
      { href: "/itinerary", label: "Itinerary builder" },
      { href: "/chat", label: "Ask the AI guide" },
      { href: "/#how", label: "How it works" },
    ],
  },
  {
    title: "About",
    links: [
      { href: "/#stories", label: "Stories from the field" },
      { href: "/#research", label: "Research project" },
      { href: "https://github.com", label: "GitHub" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="relative mt-24 border-t border-border/80 bg-jade-900 text-jade-50">
      {/* Saffron sunrise sliver */}
      <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-jade-700 via-saffron-400 to-jade-700" />
      <div className="container grid gap-12 py-16 md:grid-cols-[1.4fr_repeat(3,1fr)]">
        <div className="space-y-5">
          <Logo invert />
          <p className="max-w-sm text-sm leading-relaxed text-jade-100/80">
            An AI-powered immersive companion for travel across the Pearl of the
            Indian Ocean. Crafted as a final-year research project at the
            University of Kelaniya.
          </p>
          <div className="flex items-center gap-2 text-xs text-jade-100/70">
            <MapPin className="h-3.5 w-3.5 text-saffron-300" />
            Colombo · Kandy · Galle · 25 districts mapped
          </div>
        </div>
        {COLUMNS.map((col) => (
          <div key={col.title} className="space-y-4">
            <p className="kicker text-saffron-300 before:bg-saffron-300/60">
              {col.title}
            </p>
            <ul className="space-y-2.5">
              {col.links.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-jade-100/85 transition-colors hover:text-saffron-300"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-jade-800/80">
        <div className="container flex flex-col items-center justify-between gap-3 py-6 text-xs text-jade-100/60 md:flex-row">
          <p>
            © {new Date().getFullYear()} LankaGuide AI · Final-year research
            project · Gautham B.K.
          </p>
          <div className="flex items-center gap-4">
            <a
              href="mailto:hello@lankaguide.lk"
              className="flex items-center gap-1.5 hover:text-saffron-300"
            >
              <Mail className="h-3.5 w-3.5" /> hello@lankaguide.lk
            </a>
            <a
              href="https://github.com"
              className="flex items-center gap-1.5 hover:text-saffron-300"
            >
              <ExternalLink className="h-3.5 w-3.5" /> GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
