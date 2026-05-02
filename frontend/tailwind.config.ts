import type { Config } from "tailwindcss";

/**
 * LankaGuide design system — editorial × tropical
 *
 * Palette inspiration:
 *   • Jade   — Sri Lankan jungle canopy & tea-estate slopes
 *   • Saffron — temple flags, spices, sunset light on the rock fortresses
 *   • Sand    — beach + ancient stone backdrops
 *   • Ink     — warm near-black for editorial typography
 */
const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: { DEFAULT: "1.25rem", md: "2rem", lg: "3rem" },
      screens: { "2xl": "1440px" },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Brand scales — use directly when semantic tokens don't fit.
        jade: {
          50:  "#ECF6F1",
          100: "#D1E8DC",
          200: "#A4D2BB",
          300: "#6FB594",
          400: "#3F9670",
          500: "#1F7A55",
          600: "#0E5C45",   // primary
          700: "#0A4938",
          800: "#073629",
          900: "#04241B",
        },
        saffron: {
          50:  "#FDF3E7",
          100: "#FAE2C2",
          200: "#F4C682",
          300: "#EDA94A",
          400: "#D88B25",
          500: "#B96E12",
          600: "#94550C",   // accent ink-on-light
          700: "#6F3F09",
          800: "#4A2A06",
          900: "#2B1903",
        },
        sand: {
          50:  "#FBF7EE",
          100: "#F6EFDC",
          200: "#EDDFB7",
          300: "#E2CC8A",
          400: "#D5B65B",
          500: "#C09F3D",
        },
        ink: {
          900: "#171413",
          800: "#23201E",
          700: "#3A3633",
          600: "#5C5854",
          500: "#7A7570",
          400: "#A29D97",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        xl: "calc(var(--radius) + 4px)",
        "2xl": "calc(var(--radius) + 10px)",
        "3xl": "calc(var(--radius) + 18px)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "ui-serif", "Georgia", "serif"],
      },
      letterSpacing: {
        tightest: "-0.04em",
        kicker: "0.18em",
      },
      boxShadow: {
        soft: "0 1px 2px hsl(160 30% 12% / 0.04), 0 4px 18px -4px hsl(160 30% 12% / 0.08)",
        lift: "0 4px 8px -2px hsl(160 30% 12% / 0.06), 0 24px 48px -16px hsl(160 30% 12% / 0.18)",
        glow: "0 0 0 1px hsl(160 35% 25% / 0.15), 0 24px 60px -24px hsl(160 35% 25% / 0.35)",
        ring: "0 0 0 1px hsl(var(--border)), 0 1px 2px hsl(160 30% 12% / 0.04)",
      },
      backgroundImage: {
        "noise":
          "url(\"data:image/svg+xml;utf8,<svg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix type='matrix' values='0 0 0 0 0.06 0 0 0 0 0.04 0 0 0 0 0.02 0 0 0 0.06 0'/></filter><rect width='256' height='256' filter='url(%23n)'/></svg>\")",
        "grid-faint":
          "linear-gradient(to right, hsl(var(--border)/.6) 1px, transparent 1px), linear-gradient(to bottom, hsl(var(--border)/.6) 1px, transparent 1px)",
        "hero-gradient":
          "linear-gradient(135deg, hsl(160 60% 12%) 0%, hsl(160 50% 18%) 35%, hsl(28 75% 35%) 100%)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "marquee": {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-up": "fade-up 0.6s cubic-bezier(0.22, 1, 0.36, 1) both",
        "fade-in": "fade-in 0.4s ease-out both",
        "marquee": "marquee 38s linear infinite",
        "shimmer": "shimmer 2.4s linear infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
