"use client";

import { useState } from "react";
import { ExternalLink, Play } from "lucide-react";

/**
 * Lightweight YouTube "facade": shows the real video thumbnail with a play
 * button and only mounts the iframe once the user clicks. This means:
 *   • the section always shows a thumbnail (no black "Video unavailable" box
 *     on first paint),
 *   • the page loads fast (no eager iframes),
 *   • playback uses the privacy-friendly youtube-nocookie host.
 *
 * Thumbnail falls back hqdefault → mqdefault if maxres isn't available.
 */
export function YouTubeFacade({ id, title }: { id: string; title: string }) {
  const [playing, setPlaying] = useState(false);
  const [thumbIdx, setThumbIdx] = useState(0);

  const thumbs = [
    `https://i.ytimg.com/vi/${id}/maxresdefault.jpg`,
    `https://i.ytimg.com/vi/${id}/hqdefault.jpg`,
    `https://i.ytimg.com/vi/${id}/mqdefault.jpg`,
  ];

  return (
    <div className="overflow-hidden rounded-2xl border border-border shadow-soft">
      <div className="relative aspect-video w-full bg-ink-900">
        {playing ? (
          <iframe
            src={`https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0&modestbranding=1`}
            title={title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
            className="absolute inset-0 h-full w-full"
          />
        ) : (
          <button
            type="button"
            onClick={() => setPlaying(true)}
            aria-label={`Play video: ${title}`}
            className="group absolute inset-0 h-full w-full"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={thumbs[thumbIdx]}
              alt={title}
              loading="lazy"
              onError={() =>
                setThumbIdx((i) => Math.min(i + 1, thumbs.length - 1))
              }
              className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            <span className="absolute inset-0 bg-gradient-to-t from-black/45 via-black/10 to-transparent" />
            <span className="absolute left-1/2 top-1/2 grid h-14 w-14 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full bg-red-600 shadow-lg transition-transform duration-300 group-hover:scale-110">
              <Play className="h-6 w-6 translate-x-[2px] fill-white text-white" />
            </span>
          </button>
        )}

        {/* Always-working escape hatch: opens the video on YouTube directly,
            even if this particular video can't be embedded (age/region locked). */}
        {!playing && (
          <a
            href={`https://www.youtube.com/watch?v=${id}`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            title="Watch on YouTube"
            className="absolute right-2 top-2 z-10 inline-flex items-center gap-1 rounded-full bg-black/55 px-2.5 py-1 text-[11px] font-medium text-white backdrop-blur transition-colors hover:bg-black/75"
          >
            YouTube
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </div>
  );
}
