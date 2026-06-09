"""
Open-Meteo weather fetch + tourist-oriented alert generation (no raw API payloads in DB).
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.alerts.models import SafetyAlert
from apps.attractions.models import District

logger = logging.getLogger("lankaguide.weather_alerts")

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
WEATHER_SYNC_SOURCE = "Open-Meteo (LankaGuide)"


class WeatherAlertService:
    DISTRICTS_WITH_COORDS: dict[str, tuple[float, float]] = {
        "Colombo": (6.9271, 79.8612),
        "Kandy": (7.2906, 80.6337),
        "Galle": (6.0535, 80.2210),
        "Anuradhapura": (8.3114, 80.4037),
        "Trincomalee": (8.5874, 81.2152),
        "Ella": (6.8667, 81.0466),
        "Nuwara Eliya": (6.9497, 80.7891),
        "Jaffna": (9.6615, 80.0255),
    }

    def fetch_weather_for_district(self, district_name: str) -> dict[str, Any] | None:
        if district_name not in self.DISTRICTS_WITH_COORDS:
            return None
        lat, lng = self.DISTRICTS_WITH_COORDS[district_name]
        params = {
            "latitude": lat,
            "longitude": lng,
            "daily": ",".join(
                [
                    "precipitation_sum",
                    "weathercode",
                    "temperature_2m_max",
                    "temperature_2m_min",
                ]
            ),
            "timezone": "Asia/Colombo",
            "forecast_days": 3,
        }
        try:
            r = requests.get(
                OPEN_METEO_FORECAST,
                params=params,
                timeout=15,
                headers={"User-Agent": "LankaGuide/1.0 (weather sync)"},
            )
            r.raise_for_status()
            data = r.json()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Open-Meteo unreachable for %s: %s", district_name, exc)
            return None

        daily = data.get("daily") or {}
        times = daily.get("time") or []
        precip = daily.get("precipitation_sum") or []
        codes = daily.get("weathercode") or []
        tmax = daily.get("temperature_2m_max") or []
        tmin = daily.get("temperature_2m_min") or []
        if not times:
            return None

        forecast_3day: list[dict[str, Any]] = []
        for i, day in enumerate(times):
            forecast_3day.append(
                {
                    "date": day,
                    "weathercode": int(codes[i]) if i < len(codes) else 0,
                    "precipitation_mm": float(precip[i] if i < len(precip) else 0)
                    or 0.0,
                    "max_temp": float(tmax[i] if i < len(tmax) else 0) or 0.0,
                    "min_temp": float(tmin[i] if i < len(tmin) else 0) or 0.0,
                }
            )

        today = forecast_3day[0]
        return {
            "district": district_name,
            "today_weathercode": today["weathercode"],
            "today_precipitation_mm": today["precipitation_mm"],
            "max_temp": today["max_temp"],
            "min_temp": today["min_temp"],
            "forecast_3day": forecast_3day,
        }

    def weathercode_to_alert(
        self, weathercode: int, precipitation_mm: float
    ) -> dict[str, str] | None:
        w = int(weathercode)
        p = float(precipitation_mm or 0)

        if 71 <= w <= 77:
            return None

        if 95 <= w <= 99:
            return {
                "severity": SafetyAlert.Severity.WARNING,
                "title": "Thunderstorms possible",
                "body": (
                    "Stormy conditions are forecast. Seek shelter during "
                    "lightning, avoid exposed high ground and open water, and "
                    "recheck transport plans."
                ),
            }

        if 61 <= w <= 67:
            if p > 50:
                return {
                    "severity": SafetyAlert.Severity.DANGER,
                    "title": "Heavy rainfall expected",
                    "body": (
                        "Very heavy rain is forecast. Flash flooding or "
                        "difficult road conditions are possible—avoid low-lying "
                        "areas and allow extra travel time."
                    ),
                }
            if p > 20:
                return {
                    "severity": SafetyAlert.Severity.WARNING,
                    "title": "Significant rainfall expected",
                    "body": (
                        "Sustained rain is expected. Carry rain gear, expect "
                        "slower journeys, and monitor local advisories."
                    ),
                }
            return None

        if 80 <= w <= 82:
            if p > 15:
                return {
                    "severity": SafetyAlert.Severity.INFO,
                    "title": "Showery conditions",
                    "body": (
                        "On-and-off showers are likely. Plan short outdoor "
                        "windows and keep a light waterproof layer handy."
                    ),
                }
            return None

        return None

    def generate_ai_summary(self, district_name: str, weather_data: dict) -> str:
        if not getattr(settings, "GROQ_API_KEY", ""):
            return (
                f"Weather in {district_name}: review the outlook and pack "
                "accordingly; allow flexibility for rain if showers are expected."
            )
        try:
            from lankaguide.services.llm_client import get_llm

            model = get_llm("fast")
            system = (
                "You are a helpful travel assistant for Sri Lanka. Write a "
                "friendly, practical weather advisory for tourists in 2 "
                "sentences. Be specific and actionable."
            )
            user = (
                f"District: {district_name}. Today's weather: {weather_data!r}. "
                "Write advisory."
            )
            r = model.generate_content(
                f"{system}\n\n{user}",
                generation_config={
                    "max_output_tokens": 80,
                    "temperature": 0.35,
                },
            )
            text = (getattr(r, "text", None) or "").strip()
            if text:
                return text
        except Exception as exc:  # noqa: BLE001
            logger.warning("Groq weather advisory failed: %s", exc)
        return (
            f"Keep an eye on conditions in {district_name}—adjust outdoor plans "
            "if rain or storms are in the forecast."
        )

    def sync_weather_alerts(self) -> tuple[int, int]:
        """
        Refresh automatic weather-based alerts and retire stale rows.
        Returns (created_count, deactivated_count).
        """
        now = timezone.now()
        six_hours_ago = now - timedelta(hours=6)
        day_ago = now - timedelta(hours=24)
        created = 0

        for district_name in self.DISTRICTS_WITH_COORDS:
            weather = self.fetch_weather_for_district(district_name)
            if weather is None:
                continue

            alert_meta = self.weathercode_to_alert(
                weather["today_weathercode"],
                weather["today_precipitation_mm"],
            )
            if not alert_meta:
                continue

            district_obj = District.objects.filter(
                name__iexact=district_name
            ).first()

            recent_q = SafetyAlert.objects.filter(
                active=True,
                source_name=WEATHER_SYNC_SOURCE,
                created_at__gte=six_hours_ago,
                title=alert_meta["title"],
            )
            if district_obj is not None:
                recent_q = recent_q.filter(district=district_obj)
            else:
                recent_q = recent_q.filter(Q(district__isnull=True))
            if recent_q.exists():
                continue

            body = self.generate_ai_summary(district_name, weather)
            with transaction.atomic():
                SafetyAlert.objects.create(
                    district=district_obj,
                    title=alert_meta["title"],
                    body=body,
                    severity=alert_meta["severity"],
                    source_url="https://open-meteo.com/",
                    source_name=WEATHER_SYNC_SOURCE,
                    active=True,
                )
                created += 1

        deactivated = SafetyAlert.objects.filter(
            active=True, created_at__lt=day_ago
        ).update(active=False)

        return created, deactivated
