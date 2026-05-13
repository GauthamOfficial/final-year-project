"""Weather for the widget: OpenWeatherMap when a key is set, else Open-Meteo (free, no key)."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("lankaguide.weather")

OWM_BASE = "https://api.openweathermap.org/data/2.5"
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
CACHE_TTL = 60 * 30  # 30 min


def _openweather_key() -> str:
    return (getattr(settings, "OPENWEATHER_API_KEY", "") or "").strip()


def _wmo_description(code: int) -> str:
    """WMO weather interpretation codes (Open-Meteo)."""
    c = int(code)
    if c == 0:
        return "Clear sky"
    if c in (1, 2):
        return "Mainly clear"
    if c == 3:
        return "Overcast"
    if c in (45, 48):
        return "Fog"
    if c in (51, 53, 55, 56, 57):
        return "Drizzle"
    if c in (61, 63, 65, 66, 67, 80, 81, 82):
        return "Rain"
    if c in (71, 73, 75, 77, 85, 86):
        return "Snow"
    if c in (95, 96, 97, 99):
        return "Thunderstorm"
    return "Variable conditions"


def _fetch_open_meteo_current(lat: float, lng: float) -> dict[str, Any] | None:
    cache_key = f"weather:om:{lat:.3f}:{lng:.3f}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        r = requests.get(
            OPEN_METEO,
            params={
                "latitude": lat,
                "longitude": lng,
                "current": ",".join(
                    [
                        "temperature_2m",
                        "relative_humidity_2m",
                        "apparent_temperature",
                        "weather_code",
                        "wind_speed_10m",
                    ]
                ),
                "wind_speed_unit": "kmh",
                "timezone": "auto",
            },
            timeout=15,
            headers={"User-Agent": "LankaGuide-Weather/1.0"},
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Open-Meteo current failed: %s", exc)
        return None

    cur = data.get("current") or {}
    code = int(cur.get("weather_code") or 0)
    payload = {
        "temp_c": round(float(cur.get("temperature_2m") or 0)),
        "feels_like_c": round(float(cur.get("apparent_temperature") or 0)),
        "humidity": int(cur.get("relative_humidity_2m") or 0),
        "description": _wmo_description(code).capitalize(),
        "icon": "",  # no OWM icon; UI skips image when falsy
        "wind_kph": round(float(cur.get("wind_speed_10m") or 0), 1),
        "city": "",
        "lat": lat,
        "lng": lng,
        "fetched_at": cur.get("time") or int(time.time()),
    }
    try:
        cache.set(cache_key, payload, CACHE_TTL)
    except Exception:
        pass
    return payload


def _fetch_open_meteo_forecast(lat: float, lng: float) -> list[dict[str, Any]] | None:
    cache_key = f"weather_fc:om:{lat:.3f}:{lng:.3f}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        r = requests.get(
            OPEN_METEO,
            params={
                "latitude": lat,
                "longitude": lng,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                "forecast_days": 5,
                "timezone": "Asia/Colombo",
            },
            timeout=15,
            headers={"User-Agent": "LankaGuide-Weather/1.0"},
        )
        r.raise_for_status()
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Open-Meteo forecast failed: %s", exc)
        return None

    daily = data.get("daily") or {}
    times = daily.get("time") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    codes = daily.get("weather_code") or []

    out: list[dict[str, Any]] = []
    for i, date in enumerate(times[:5]):
        code = int(codes[i] if i < len(codes) else 0)
        out.append(
            {
                "date": date,
                "temp_min_c": round(float(tmin[i] if i < len(tmin) else 0)),
                "temp_max_c": round(float(tmax[i] if i < len(tmax) else 0)),
                "description": _wmo_description(code).capitalize(),
                "icon": "",
            }
        )
    try:
        cache.set(cache_key, out, CACHE_TTL)
    except Exception:
        pass
    return out


def _try_openweather_current(lat: float, lng: float) -> dict[str, Any] | None:
    api_key = _openweather_key()
    if not api_key:
        return None

    cache_key = f"weather:owm:{lat:.3f}:{lng:.3f}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        r = requests.get(
            f"{OWM_BASE}/weather",
            params={"lat": lat, "lon": lng, "units": "metric", "appid": api_key},
            timeout=10,
        )
        if not r.ok:
            try:
                body = r.json()
                err = body.get("message", r.text[:200])
            except Exception:
                err = r.text[:200]
            logger.warning(
                "OpenWeatherMap /weather HTTP %s: %s",
                r.status_code,
                err,
            )
            return None
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenWeatherMap current request failed: %s", exc)
        return None

    weather = (data.get("weather") or [{}])[0]
    main = data.get("main") or {}
    wind = data.get("wind") or {}
    payload = {
        "temp_c": round(main.get("temp", 0)),
        "feels_like_c": round(main.get("feels_like", 0)),
        "humidity": main.get("humidity"),
        "description": (weather.get("description") or "").capitalize(),
        "icon": weather.get("icon") or "",
        "wind_kph": round((wind.get("speed") or 0) * 3.6, 1),
        "city": data.get("name") or "",
        "lat": lat,
        "lng": lng,
        "fetched_at": data.get("dt"),
    }
    try:
        cache.set(cache_key, payload, CACHE_TTL)
    except Exception:
        pass
    return payload


def _try_openweather_forecast(lat: float, lng: float) -> list[dict[str, Any]] | None:
    api_key = _openweather_key()
    if not api_key:
        return None

    cache_key = f"weather_fc:owm:{lat:.3f}:{lng:.3f}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        r = requests.get(
            f"{OWM_BASE}/forecast",
            params={
                "lat": lat,
                "lon": lng,
                "units": "metric",
                "appid": api_key,
                "cnt": 40,
            },
            timeout=10,
        )
        if not r.ok:
            logger.warning("OpenWeatherMap /forecast HTTP %s", r.status_code)
            return None
        data = r.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("OpenWeatherMap forecast failed: %s", exc)
        return None

    by_day: dict[str, list[dict]] = {}
    for entry in data.get("list", []):
        date = (entry.get("dt_txt") or "")[:10]
        if date:
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
                "icon": icon or "",
            }
        )
    try:
        cache.set(cache_key, out, CACHE_TTL)
    except Exception:
        pass
    return out


def fetch_current(lat: float, lng: float) -> dict[str, Any] | None:
    """Preferred: OpenWeatherMap with valid key; fallback: Open-Meteo (no key)."""
    owm = _try_openweather_current(lat, lng)
    if owm:
        return owm
    return _fetch_open_meteo_current(lat, lng)


def fetch_forecast(lat: float, lng: float) -> list[dict[str, Any]] | None:
    owm = _try_openweather_forecast(lat, lng)
    if owm:
        return owm
    return _fetch_open_meteo_forecast(lat, lng)
