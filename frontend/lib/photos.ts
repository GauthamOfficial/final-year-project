/**
 * Curated Sri Lanka photography for marketing sections.
 *
 * Local `public/` assets are only used when the destination slug has a
 * dedicated mapping in `getLocalImageForSlug` (no image reuse).
 */

import { getLocalImageForSlug } from "@/lib/local-attraction-images";

const u = (id: string, w = 1600, q = 75) =>
  `https://images.unsplash.com/photo-${id}?auto=format&fit=crop&w=${w}&q=${q}`;
const wm = (fileName: string) =>
  `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(fileName)}`;

function photoForSlug(slug: string, fallback: string): string {
  return getLocalImageForSlug(slug) || fallback;
}

export const HERO_PHOTOS = {
  // Committed local Sigiriya photo (Wikimedia Commons, CC) — no remote
  // dependency for the LCP hero image.
  sigiriya: "/hero-sigiriya.webp",
  teaEstate: u("1566303662030-fcb610b14454", 2000),
  stiltFishermen: u("1546708973-c6741ba56f6d", 2000),
};

export type FeaturedDestination = {
  slug: string;
  name: string;
  region: string;
  category: "Cultural" | "Wildlife" | "Beach" | "Highlands" | "Religious" | "Adventure";
  blurb: string;
  photo: string;
  span: "lg" | "md" | "sm";
};

export const FEATURED_DESTINATIONS: FeaturedDestination[] = [
  {
    slug: "sigiriya-rock-fortress-matale",
    name: "Sigiriya",
    region: "Matale · Cultural Triangle",
    category: "Cultural",
    blurb:
      "Climb the 5th-century rock palace King Kashyapa carved into a 200m granite monolith.",
    photo: photoForSlug(
      "sigiriya-rock-fortress-matale",
      u("1593693411515-c20261bcad6e", 2000)
    ),
    span: "lg",
  },
  {
    slug: "nine-arches-bridge-badulla",
    name: "Ella Highlands",
    region: "Badulla",
    category: "Highlands",
    blurb: "Misty tea slopes, Nine Arches viaduct sunrise, Little Adam's Peak.",
    photo: photoForSlug(
      "nine-arches-bridge-badulla",
      u("1566303662030-fcb610b14454", 2000)
    ),
    span: "md",
  },
  {
    slug: "yala-national-park-hambantota",
    name: "Yala",
    region: "Hambantota",
    category: "Wildlife",
    blurb: "Densest leopard population on earth — best months Feb to July.",
    photo: photoForSlug(
      "yala-national-park-hambantota",
      wm("Yala national park beach area.jpg")
    ),
    span: "md",
  },
  {
    slug: "galle-fort-galle",
    name: "Galle Fort",
    region: "Galle",
    category: "Cultural",
    blurb: "A walled Dutch enclave overlooking the Indian Ocean.",
    photo: photoForSlug("galle-fort-galle", wm("Lighthouse Galle, Sri Lanka.jpg")),
    span: "sm",
  },
  {
    slug: "mirissa-whale-watching-matara",
    name: "Mirissa",
    region: "Matara · Southern Coast",
    category: "Beach",
    blurb: "Crescent palms, blue whale migrations, twilight bonfires.",
    photo: photoForSlug(
      "mirissa-whale-watching-matara",
      wm("View from Coconut Tree Hill to Mirissa in March.jpg")
    ),
    span: "sm",
  },
  {
    slug: "temple-of-the-sacred-tooth-relic-kandy",
    name: "Temple of the Tooth",
    region: "Kandy",
    category: "Religious",
    blurb: "The relic-shrine that crowns Sri Lanka's last royal capital.",
    photo: photoForSlug(
      "temple-of-the-sacred-tooth-relic-kandy",
      wm("Front view of Temple of the Tooth, Kandy.jpg")
    ),
    span: "sm",
  },
];

export const STORY_PHOTOS = [
  u("1602002418679-4eedb19f7b2a", 800),
  u("1583499871880-0e7ce5a78416", 800),
  u("1605649461784-4f53354c0d70", 800),
];
