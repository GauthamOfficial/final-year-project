"use client";

import { useEffect } from "react";
import dynamic from "next/dynamic";
import "leaflet/dist/leaflet.css";

const MapContainer = dynamic(
  () => import("react-leaflet").then((m) => m.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import("react-leaflet").then((m) => m.TileLayer),
  { ssr: false }
);
const Marker = dynamic(
  () => import("react-leaflet").then((m) => m.Marker),
  { ssr: false }
);
const Popup = dynamic(
  () => import("react-leaflet").then((m) => m.Popup),
  { ssr: false }
);
const Polyline = dynamic(
  () => import("react-leaflet").then((m) => m.Polyline),
  { ssr: false }
);

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
  useEffect(() => {
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
    })();
  }, []);

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

  const center: [number, number] = [stops[0].lat, stops[0].lng];

  return (
    <div
      className="overflow-hidden rounded-3xl border border-border shadow-soft"
      style={{ height }}
    >
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {stops.map((s) => (
          <Marker key={s.id} position={[s.lat, s.lng]}>
            <Popup>{s.name}</Popup>
          </Marker>
        ))}
        {showLine && stops.length > 1 && (
          <Polyline
            positions={stops.map((s) => [s.lat, s.lng])}
            pathOptions={{ color: "#0F3C2E", weight: 3, opacity: 0.7 }}
          />
        )}
      </MapContainer>
    </div>
  );
}
