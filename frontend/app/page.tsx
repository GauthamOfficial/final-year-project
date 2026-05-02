import { ClosingCta } from "@/components/marketing/cta";
import { FeaturedDestinations } from "@/components/marketing/featured-destinations";
import { Hero } from "@/components/marketing/hero";
import { HowItWorks } from "@/components/marketing/how-it-works";
import { StatsBand } from "@/components/marketing/stats-band";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";

export default function HomePage() {
  return (
    <>
      <SiteHeader transparentTop />
      <main>
        <Hero />
        <FeaturedDestinations />
        <StatsBand />
        <HowItWorks />
        <ClosingCta />
      </main>
      <SiteFooter />
    </>
  );
}
