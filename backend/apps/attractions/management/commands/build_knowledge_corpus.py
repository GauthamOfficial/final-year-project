"""
`python manage.py build_knowledge_corpus`

For every Attraction in the database, write a curated knowledge file under
`backend/data/knowledge/<district_id>__<attraction_id>__<category>__<slug>.txt`.

The file format is the deterministic structure that `ingest_knowledge_base`
expects, so once this command finishes you can run:

    python manage.py ingest_knowledge_base --reset

…to refresh ChromaDB. The text body is built from the curated database
fields (no third-party calls, no hallucinations). Optional Wikipedia lead
extract is appended verbatim if available, with attribution.

Idempotent — rerun whenever you update the attraction descriptions.
"""

from __future__ import annotations

import logging
from pathlib import Path

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.attractions.models import Attraction

logger = logging.getLogger("lankaguide.knowledge.build")

WIKI_API = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "LankaGuide/1.0 (https://lankaguide.lk; ops@lankaguide.lk)"

CATEGORY_BLURB = {
    "cultural": "cultural / heritage site",
    "religious": "religious site",
    "wildlife": "wildlife / safari experience",
    "beach": "beach / coastal experience",
    "adventure": "adventure / outdoor activity",
    "food": "food / culinary experience",
}

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


class Command(BaseCommand):
    help = "Build per-attraction knowledge files for ChromaDB ingestion."

    def add_arguments(self, parser):
        parser.add_argument(
            "--district", type=str, default=None,
            help="Only process attractions in this district name."
        )
        parser.add_argument(
            "--no-wiki", action="store_true",
            help="Skip the Wikipedia lead extract."
        )
        parser.add_argument(
            "--out",
            default=str(Path(settings.BASE_DIR) / "data" / "knowledge"),
            help="Output directory.",
        )

    def handle(self, *args, **opts):
        out_dir = Path(opts["out"])
        out_dir.mkdir(parents=True, exist_ok=True)

        qs = Attraction.objects.select_related("district").order_by(
            "district__name", "name"
        )
        if opts.get("district"):
            qs = qs.filter(district__name__iexact=opts["district"])

        written = 0
        for a in qs:
            slug = slugify(a.slug or a.name)
            stem = (
                f"{a.district_id}__{a.id}__{a.category}__{slug}"
            )
            target = out_dir / f"{stem}.txt"
            text = self._render(a, include_wiki=not opts["no_wiki"])
            target.write_text(text, encoding="utf-8")
            written += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote {written} knowledge files into {out_dir}."
            )
        )

    def _render(self, a: Attraction, *, include_wiki: bool) -> str:
        district = a.district
        category_label = CATEGORY_BLURB.get(a.category, a.category)
        seasons = ", ".join(MONTH_NAMES[m - 1] for m in (a.best_season or []))
        district_peaks = ", ".join(
            MONTH_NAMES[m - 1] for m in (district.peak_months or [])
        )

        sections = [
            f"# {a.name}",
            "",
            f"**District:** {district.name} ({district.province} Province)",
            f"**Category:** {category_label}",
            f"**Best months to visit:** {seasons or 'any time'}",
            (
                f"**District peak season:** {district_peaks}" if district_peaks else ""
            ),
            f"**Climate zone:** {district.climate_zone}",
            (
                f"**Entry fee (LKR, indicative):** {a.entry_fee_lkr}"
                if a.entry_fee_lkr is not None and a.entry_fee_lkr > 0
                else "**Entry fee:** Free"
            ),
            "",
            "## Overview",
            a.description.strip(),
            "",
        ]

        sections += [
            "## Practical tips",
            self._tip(a),
            "",
            "## How to get there",
            self._directions(a),
            "",
        ]

        if include_wiki and a.wikipedia_title:
            extract = self._wiki_extract(a.wikipedia_title)
            if extract:
                sections += [
                    "## Background (excerpted from Wikipedia)",
                    extract,
                    "",
                    f"_Source: https://en.wikipedia.org/wiki/{a.wikipedia_title.replace(' ', '_')}_",
                    "",
                ]

        sections += [
            "## Quick facts",
            f"- ID: {a.id}",
            f"- Slug: {a.slug}",
            f"- Coordinates: {a.lat}, {a.lng}",
            f"- District: {district.name} (id {district.id})",
        ]

        return "\n".join(s for s in sections if s is not None)

    @staticmethod
    def _tip(a: Attraction) -> str:
        notes: list[str] = []
        if a.category == "wildlife":
            notes.append(
                "Book a 4WD safari with a registered tracker. Mornings (06:00-09:30) "
                "and late afternoons (15:30-18:00) give the best wildlife viewing; "
                "midday is hot and animals retreat to shade."
            )
        elif a.category == "beach":
            notes.append(
                "Reef shoes help on rocky coves; surf currents can be strong, "
                "especially May-September on the south coast and December-March on the east."
            )
        elif a.category == "religious":
            notes.append(
                "Cover shoulders and knees, remove shoes and hats, and refrain from "
                "posing with your back to Buddha statues. Many sites do not allow drones."
            )
        elif a.category == "cultural":
            notes.append(
                "Bring water and a wide-brimmed hat; ancient cities offer little shade. "
                "Most sites accept photography for personal use without a fee."
            )
        elif a.category == "adventure":
            notes.append(
                "Tell someone your route, pack a head torch and starting before "
                "dawn beats both heat and the after-school crowds."
            )
        else:
            notes.append("Carry small denominations of LKR for tickets and tips.")
        return "- " + "\n- ".join(notes)

    @staticmethod
    def _directions(a: Attraction) -> str:
        district = a.district
        return (
            f"Most travellers reach {a.name} via {district.name} town. From "
            f"Colombo it is roughly {_distance_estimate(district.name)} by road; "
            f"public buses run daily from Pettah, and intercity trains serve "
            f"the major hill-country and coastal districts. Tuk-tuks cover the "
            f"last mile from {district.name} town."
        )

    def _wiki_extract(self, title: str) -> str:
        try:
            r = requests.get(
                WIKI_API,
                headers={"User-Agent": USER_AGENT},
                params={
                    "action": "query",
                    "format": "json",
                    "prop": "extracts",
                    "explaintext": "1",
                    "exintro": "1",
                    "redirects": "1",
                    "titles": title,
                },
                timeout=15,
            )
            r.raise_for_status()
            pages = (r.json().get("query", {}) or {}).get("pages", {}) or {}
            for _, page in pages.items():
                extract = (page.get("extract") or "").strip()
                if extract:
                    return extract[:1200]
        except Exception as exc:  # noqa: BLE001
            logger.debug("wiki extract failed for %s: %s", title, exc)
        return ""


# Rough straight-line distance estimates from Colombo to each district capital.
def _distance_estimate(district_name: str) -> str:
    table = {
        "Colombo": "0 km", "Gampaha": "30 km", "Kalutara": "45 km",
        "Kandy": "115 km", "Matale": "140 km", "Nuwara Eliya": "180 km",
        "Galle": "120 km", "Matara": "160 km", "Hambantota": "240 km",
        "Jaffna": "400 km", "Kilinochchi": "330 km", "Mannar": "320 km",
        "Vavuniya": "260 km", "Mullaitivu": "335 km",
        "Batticaloa": "310 km", "Ampara": "330 km", "Trincomalee": "260 km",
        "Kurunegala": "95 km", "Puttalam": "135 km",
        "Anuradhapura": "205 km", "Polonnaruwa": "215 km",
        "Badulla": "220 km", "Moneragala": "240 km",
        "Ratnapura": "100 km", "Kegalle": "80 km",
    }
    return table.get(district_name, "a few hours")
