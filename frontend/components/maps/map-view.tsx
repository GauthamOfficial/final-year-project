"use client";

import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";

export type MapStop = {
  id: number | string;
  name: string;
  lat: number;
  lng: number;
};

export function MapView({
  stops,
  height = 360,
  zoom = 8,
  showLine = true,
}: {
  stops: MapStop[];
  height?: number;
  zoom?: number;
  showLine?: boolean;
}) {
  const mapRef = useRef<import("leaflet").Map | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!stops.length || !containerRef.current) return;

    let cancelled = false;
    const mountEl = containerRef.current;
    if (!mountEl) return;
    (async () => {
      const L = (await import("leaflet")).default;
      type IconProto = { _getIconUrl?: unknown };
      delete (L.Icon.Default.prototype as IconProto)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
        iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
        shadowUrl:
          "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
      });

      if (cancelled) return;

      // HMR/StrictMode safety: ensure stale container stamp is cleared.
      const stampTarget = mountEl as { _leaflet_id?: unknown };
      if (stampTarget._leaflet_id) {
        try {
          delete stampTarget._leaflet_id;
        } catch {
          stampTarget._leaflet_id = undefined;
        }
      }

      const center: [number, number] = [stops[0].lat, stops[0].lng];
      const map = L.map(mountEl, { scrollWheelZoom: false, zoomControl: true }).setView(
        center,
        zoom
      );
      mapRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(map);

      const latlngs: Array<[number, number]> = stops.map((s) => [s.lat, s.lng]);

      stops.forEach((s) => {
        L.marker([s.lat, s.lng]).addTo(map).bindPopup(s.name);
      });

      if (showLine && latlngs.length > 1) {
        L.polyline(latlngs, {
          color: "#0F3C2E",
          weight: 3,
          opacity: 0.7,
        }).addTo(map);
      }

      if (latlngs.length > 1) {
        map.fitBounds(L.latLngBounds(latlngs), { padding: [24, 24] });
      }

      // Ensure proper sizing after container is painted.
      requestAnimationFrame(() => map.invalidateSize());
    })();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;

      const stampTarget = mountEl as { _leaflet_id?: unknown };
      if (stampTarget._leaflet_id) {
        try {
          delete stampTarget._leaflet_id;
        } catch {
          stampTarget._leaflet_id = undefined;
        }
      }
    };
  }, [stops, zoom, showLine]);

  if (!stops.length) {
    return (
      <div
        className="grid place-items-center rounded-3xl border border-dashed border-border bg-muted text-sm text-ink-500"
        style={{ height }}
      >
        No coordinates available.
      </div>
    );
  }

  return (
    <div
      className="overflow-hidden rounded-3xl border border-border shadow-soft"
      style={{ height }}
    >
      <div ref={containerRef} className="h-full w-full" />
    </div>
  );
}
