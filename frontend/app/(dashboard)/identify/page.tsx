import Link from "next/link";
import { ArrowLeft, Camera, Sparkles } from "lucide-react";
import { LandmarkIdentifier } from "@/components/vision/LandmarkIdentifier";

export const metadata = {
  title: "Landmark identification · LankaGuide",
  description:
    "Upload a photo of a Sri Lankan landmark. AI identifies it, links to our attraction guide, and adds a short sourced summary from the knowledge base.",
};

export default function IdentifyPage() {
  return (
    <div className="container max-w-3xl py-12 md:py-16">
      <div className="mb-8">
        <Link
          href="/explore"
          className="inline-flex items-center gap-1 text-sm font-medium text-jade-700 hover:text-jade-800"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to explore
        </Link>
      </div>

      <header className="mb-10 text-center md:text-left">
        <span className="kicker">
          <Camera className="h-3 w-3" />
          Landmark ID
        </span>
        <h1 className="display mt-4 text-3xl font-medium tracking-tightest text-ink-900 md:text-5xl">
          Name that{" "}
          <em className="text-jade-700 not-italic">temple, stupa, or view</em>
        </h1>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-ink-600">
          We validate your photo in the browser, then match it to our atlas of
          curated attractions. When it succeeds, you get a visitor-friendly
          blurb with citations from the LankaGuide corpus.
        </p>
        <p className="mt-2 flex flex-wrap items-center justify-center gap-2 text-xs text-ink-500 md:justify-start">
          <Sparkles className="h-3.5 w-3.5 text-saffron-600" />
          JPG, PNG or WEBP · up to 10MB · rate-limited on the server
        </p>
      </header>

      <LandmarkIdentifier className="max-w-xl md:mx-0" />
    </div>
  );
}
