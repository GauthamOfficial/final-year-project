"""OSRM (free public router) + a simple congestion heuristic."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("lankaguide.routing")

CACHE_TTL = 60 * 60  # 1 hour

# Heuristic congestion multipliers — applied to free-flow OSRM duration.
# Multiplier of 1.0 = no extra delay. Tuned conservatively from anecdotal
# Sri Lanka driving observations.
def _congestion_multiplier(district_a: str | None, district_b: str | None,
                           dt: datetime) -> tuple[float, str]:
    weekday = dt.weekday()  # 0 Mon .. 6 Sun
    hour = dt.hour
    is_weekday = weekday < 5
    rush = is_weekday and (7 <= hour <= 9 or 16 <= hour <= 19)

    if "Colombo" in (district_a or "", district_b or ""):
        if rush:
            return 1.55, "Heavy"
        return 1.30, "Moderate"
    if "Kandy" in (district_a or "", district_b or "") and rush:
        return 1.35, "Moderate"
    if not is_weekday and (
        "Galle" in (district_a or "", district_b or "")
        or "Matara" in (district_a or "", district_b or "")
        or "Mirissa" in (district_a or "", district_b or "")
    ):
        return 1.25, "Moderate"
    return 1.10, "Light"


def _format_duration(seconds: float) -> str:
    secs = int(seconds)
    h = secs // 3600
    m = (secs % 3600) // 60
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def get_route(
    from_lat: float, from_lng: float,
    to_lat: float, to_lng: float,
    *,
    district_a: str | None = None,
    district_b: str | None = None,
) -> dict[str, Any] | None:
    cache_key = f"osrm:{from_lat:.3f},{from_lng:.3f}->{to_lat:.3f},{to_lng:.3f}"
    cached = cache.get(cache_key)
    if cached:
        cached = dict(cached)
    else:
        url = (
            f"{settings.OSRM_BASE_URL}/route/v1/driving/"
            f"{from_lng},{from_lat};{to_lng},{to_lat}"
        )
        try:
            r = requests.get(
                url,
                params={"overview": "simplified", "geometries": "geojson"},
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("OSRM fetch failed: %s", exc)
            return None
        routes = data.get("routes") or []
        if not routes:
            return None
        route = routes[0]
        cached = {
            "distance_km": round((route.get("distance") or 0) / 1000.0, 1),
            "duration_seconds": route.get("duration") or 0,
            "geometry": route.get("geometry"),
        }
        try:
            cache.set(cache_key, cached, CACHE_TTL)
        except Exception:
            pass

    multiplier, traffic_label = _congestion_multiplier(district_a, district_b, datetime.now())
    free_flow = cached["duration_seconds"]
    eta_seconds = free_flow * multiplier
    cached.update(
        {
            "free_flow_duration_text": _format_duration(free_flow),
            "estimated_duration_text": _format_duration(eta_seconds),
            "estimated_duration_seconds": round(eta_seconds),
            "congestion_multiplier": multiplier,
            "traffic_label": traffic_label,
            "estimate_disclaimer": (
                "Estimate based on free-flow drive time + a time-of-day "
                "heuristic. Actual conditions may vary."
            ),
        }
    )
    return cached
