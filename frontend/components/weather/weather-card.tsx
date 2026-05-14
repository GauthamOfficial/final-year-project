"use client";

import { useEffect, useState } from "react";
import { Cloud, Droplets, Wind } from "lucide-react";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

type Current = {
  temp_c: number;
  feels_like_c: number;
  humidity: number;
  description: string;
  icon: string;
  wind_kph: number;
  city: string;
};

type Forecast = {
  date: string;
  temp_min_c: number;
  temp_max_c: number;
  description: string;
  icon: string;
};

function WeatherCardSkeleton() {
  return (
    <div
      className="rounded-3xl border border-border bg-white p-5 shadow-soft"
      aria-busy="true"
      aria-label="Loading weather"
    >
      <div className="flex items-center gap-3">
        <Skeleton className="h-14 w-14 shrink-0 rounded-xl" />
        <div className="min-w-0 flex-1 space-y-2">
          <Skeleton className="h-9 w-24 rounded-md" />
          <Skeleton className="h-3 w-48 max-w-full rounded-md" />
        </div>
      </div>
      <div className="mt-3 flex items-center gap-4">
        <Skeleton className="h-3 w-24 rounded-md" />
        <Skeleton className="h-3 w-14 rounded-md" />
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 sm:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="flex flex-col items-center gap-2 rounded-xl bg-jade-50/80 p-2"
          >
            <Skeleton className="h-2.5 w-9 rounded-md" />
            <Skeleton className="h-8 w-8 rounded-md" />
            <Skeleton className="h-3 w-14 rounded-md" />
          </div>
        ))}
      </div>
    </div>
  );
}

export function WeatherCard({ districtId }: { districtId: number | null }) {
  const [current, setCurrent] = useState<Current | null>(null);
  const [forecast, setForecast] = useState<Forecast[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!districtId) {
      setCurrent(null);
      setForecast([]);
      setErr(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setErr(null);
    setCurrent(null);
    setForecast([]);
    api
      .get(`/api/v1/weather/?district_id=${districtId}`)
      .then(({ data }) => {
        if (cancelled) return;
        if (!data?.current) {
          setErr("Weather unavailable.");
          return;
        }
        setCurrent(data.current);
        setForecast(data.forecast || []);
      })
      .catch((e) => {
        if (cancelled) return;
        const msg = e?.response?.data?.detail || "Weather unavailable.";
        setErr(msg);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [districtId]);

  if (!districtId) {
    return null;
  }

  if (err) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-muted p-4 text-xs text-ink-500">
        <Cloud className="mb-2 h-4 w-4" /> {err}
      </div>
    );
  }

  if (loading || !current) {
    return <WeatherCardSkeleton />;
  }

  return (
    <div className="rounded-3xl border border-border bg-white p-5 shadow-soft">
      <div className="flex items-center gap-3">
        {current.icon && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={`https://openweathermap.org/img/wn/${current.icon}@2x.png`}
            alt=""
            className="h-14 w-14"
          />
        )}
        <div>
          <p className="display text-3xl font-medium leading-none text-ink-900">
            {current.temp_c}°C
          </p>
          <p className="text-xs text-ink-600">
            {current.description} · feels {current.feels_like_c}°C
          </p>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-ink-500">
        <span className="flex items-center gap-1">
          <Wind className="h-3 w-3" /> {current.wind_kph} km/h
        </span>
        <span className="flex items-center gap-1">
          <Droplets className="h-3 w-3" /> {current.humidity}%
        </span>
      </div>
      {forecast.length > 0 && (
        <div className="mt-4 grid grid-cols-3 gap-2 sm:grid-cols-5">
          {forecast.map((f) => (
            <div
              key={f.date}
              className="rounded-xl bg-jade-50 p-2 text-center"
              title={f.description}
            >
              <p className="text-[10px] font-semibold uppercase tracking-kicker text-ink-500">
                {new Date(f.date).toLocaleDateString(undefined, {
                  weekday: "short",
                })}
              </p>
              {f.icon && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={`https://openweathermap.org/img/wn/${f.icon}.png`}
                  alt=""
                  className="mx-auto h-8 w-8"
                />
              )}
              <p className="text-xs font-semibold text-ink-900">
                {f.temp_max_c}° / {f.temp_min_c}°
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
