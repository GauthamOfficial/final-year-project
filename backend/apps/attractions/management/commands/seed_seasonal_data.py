"""Seed monthly crowd/weather curves for every attraction from district province (Gap 8)."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from ...models import Attraction, ClimateZone, SeasonalData

WET_ZONE_MONTHS = {
    1: (4, 4),
    2: (5, 5),
    3: (7, 4),
    4: (6, 3),
    5: (4, 2),
    6: (3, 2),
    7: (3, 2),
    8: (3, 2),
    9: (3, 2),
    10: (4, 3),
    11: (5, 3),
    12: (6, 4),
}

DRY_ZONE_MONTHS = {
    1: (5, 3),
    2: (6, 4),
    3: (8, 5),
    4: (9, 5),
    5: (8, 5),
    6: (7, 5),
    7: (6, 4),
    8: (5, 4),
    9: (4, 3),
    10: (3, 2),
    11: (3, 2),
    12: (4, 3),
}

CENTRAL_MONTHS = {
    1: (7, 5),
    2: (8, 5),
    3: (9, 5),
    4: (7, 4),
    5: (5, 3),
    6: (4, 3),
    7: (6, 4),
    8: (5, 3),
    9: (4, 3),
    10: (5, 3),
    11: (6, 4),
    12: (8, 5),
}

UVA_MONTHS = {
    1: (6, 5),
    2: (7, 5),
    3: (8, 4),
    4: (6, 3),
    5: (4, 2),
    6: (3, 2),
    7: (7, 5),
    8: (6, 5),
    9: (4, 3),
    10: (3, 2),
    11: (4, 3),
    12: (5, 4),
}


def _calendar_for_district(district) -> dict[int, tuple[int, int]]:
    province = (district.province or "").lower()
    climate = district.climate_zone or ClimateZone.WET

    if "uva" in province:
        return UVA_MONTHS
    if "central" in province:
        return CENTRAL_MONTHS
    if any(
        p in province
        for p in ("western", "southern", "sabaragamuwa")
    ):
        return WET_ZONE_MONTHS
    if any(p in province for p in ("northern", "eastern", "north central")):
        return DRY_ZONE_MONTHS

    if climate == ClimateZone.DRY:
        return DRY_ZONE_MONTHS
    if climate == ClimateZone.WET:
        return WET_ZONE_MONTHS
    return CENTRAL_MONTHS


def _visitor_note(crowd: float, weather: int) -> str:
    parts: list[str] = []
    if weather <= 2:
        parts.append("Monsoon season — expect rain and muddy paths")
    if crowd >= 9:
        parts.append("Peak tourist season — book accommodation in advance")
    return " ".join(parts)[:200]


class Command(BaseCommand):
    help = "Replace all SeasonalData rows with province-based monthly curves."

    def handle(self, *args, **options):
        deleted, _ = SeasonalData.objects.all().delete()
        self.stdout.write(f"Cleared {deleted} existing seasonal row(s).")

        qs = Attraction.objects.select_related("district").order_by("id")
        total = qs.count()
        created = 0

        for i, attraction in enumerate(qs.iterator(), start=1):
            cal = _calendar_for_district(attraction.district)
            batch: list[SeasonalData] = []
            for month in range(1, 13):
                crowd_f, weather = cal[month]
                crowd = float(crowd_f)
                is_peak = crowd >= 7.0
                batch.append(
                    SeasonalData(
                        attraction=attraction,
                        month=month,
                        crowd_index=crowd,
                        weather_rating=weather,
                        is_peak_season=is_peak,
                        visitor_note=_visitor_note(crowd, weather),
                    )
                )
            SeasonalData.objects.bulk_create(batch)
            created += len(batch)
            self.stdout.write(
                self.style.SUCCESS(
                    f"[{i}/{total}] {attraction.name} — 12 months ({attraction.district.province})"
                )
            )

        self.stdout.write(self.style.SUCCESS(f"Done. Created {created} SeasonalData rows."))
