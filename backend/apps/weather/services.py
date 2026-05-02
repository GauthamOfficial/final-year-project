"""OpenWeatherMap (free) wrapper for the weather widget."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("lankaguide.weather")

OWM_BASE = "https://api.openweathermap.org/data/2.5"
CACHE_TTL = 60 * 30  # 30 min


def fetch_current(lat: float, lng: float) -> dict[str, Any] | None:
    """Returns a normalised weather payload or None if the API is down/unkeyed."""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return None

    cache_key = f"weather:{lat:.3f}:{lng:.3f}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        r = requests.get(
            f"{OWM_BASE}/weather",
            params={"lat": lat, "lon": lng, "units": "metric", "appid": api_key},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("weather fetch failed: %s", exc)
        return None

    weather = (data.get("weather") or [{}])[0]
    main = data.get("main") or {}
    wind = data.get("wind") or {}
    payload = {
        "temp_c": round(main.get("temp", 0)),
        "feels_like_c": round(main.get("feels_like", 0)),
        "humidity": main.get("humidity"),
        "description": (weather.get("description") or "").capitalize(),
        "icon": weather.get("icon"),
        "wind_kph": round((wind.get("speed") or 0) * 3.6, 1),
        "city": data.get("name"),
        "lat": lat,
        "lng": lng,
        "fetched_at": data.get("dt"),
    }
    try:
        cache.set(cache_key, payload, CACHE_TTL)
    except Exception:
        pass
    return payload


def fetch_forecast(lat: float, lng: float) -> list[dict[str, Any]] | None:
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return None

    cache_key = f"weather_fc:{lat:.3f}:{lng:.3f}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        r = requests.get(
            f"{OWM_BASE}/forecast",
            params={"lat": lat, "lon": lng, "units": "metric", "appid": api_key, "cnt": 8 * 5},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("forecast fetch failed: %s", exc)
        return None

    # Aggregate to 5 daily averages
    by_day: dict[str, list[dict]] = {}
    for entry in data.get("list", []):
        date = entry.get("dt_txt", "")[:10]
        by_day.setdefault(date, []).append(entry)

    out: list[dict[str, Any]] = []
    for date, entries in list(by_day.items())[:5]:
        temps = [e["main"]["temp"] for e in entries]
        descs = [(e["weather"] or [{}])[0].get("description", "") for e in entries]
        icon = (entries[len(entries) // 2]["weather"] or [{}])[0].get("icon")
        out.append(
            {
                "date": date,
                "temp_min_c": round(min(temps)),
                "temp_max_c": round(max(temps)),
                "description": max(set(descs), key=descs.count).capitalize(),
                "icon": icon,
            }
        )
    try:
        cache.set(cache_key, out, CACHE_TTL)
    except Exception:
        pass
    return out
