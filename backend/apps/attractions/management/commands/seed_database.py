"""
`python manage.py seed_database` — Prompt 3B.

Populates `districts` with all 25 Sri Lanka districts (name, province,
lat/lng, climate_zone, peak_months) and inserts 10 sample attractions per
priority district (Colombo, Kandy, Galle, Matale, Badulla — the latter two
covering Sigiriya and Ella respectively per PRD §3B). Other districts get
3-5 lightweight stubs so the Explorer (Prompt 5C) has content everywhere.

Re-run safely: `--flush` wipes attractions/districts before seeding.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.attractions.models import (
    Attraction,
    AttractionCategory,
    ClimateZone,
    District,
)

# ─────────────────────────── Reference Data ────────────────────────────
DISTRICTS: list[dict] = [
    {"name": "Colombo", "province": "Western", "lat": 6.9271, "lng": 79.8612, "climate": ClimateZone.WET, "peak": [12, 1, 2, 3, 7, 8]},
    {"name": "Gampaha", "province": "Western", "lat": 7.0917, "lng": 79.9999, "climate": ClimateZone.WET, "peak": [12, 1, 2, 3]},
    {"name": "Kalutara", "province": "Western", "lat": 6.5854, "lng": 79.9607, "climate": ClimateZone.WET, "peak": [12, 1, 2, 3]},
    {"name": "Kandy", "province": "Central", "lat": 7.2906, "lng": 80.6337, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 7, 8]},
    {"name": "Matale", "province": "Central", "lat": 7.4675, "lng": 80.6234, "climate": ClimateZone.INTERMEDIATE, "peak": [5, 6, 7, 8, 9]},
    {"name": "Nuwara Eliya", "province": "Central", "lat": 6.9497, "lng": 80.7891, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 4, 8]},
    {"name": "Galle", "province": "Southern", "lat": 6.0535, "lng": 80.2210, "climate": ClimateZone.WET, "peak": [12, 1, 2, 3]},
    {"name": "Matara", "province": "Southern", "lat": 5.9485, "lng": 80.5353, "climate": ClimateZone.WET, "peak": [12, 1, 2, 3, 4]},
    {"name": "Hambantota", "province": "Southern", "lat": 6.1241, "lng": 81.1185, "climate": ClimateZone.DRY, "peak": [2, 3, 4, 5, 6, 7]},
    {"name": "Jaffna", "province": "Northern", "lat": 9.6615, "lng": 80.0255, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8, 9]},
    {"name": "Kilinochchi", "province": "Northern", "lat": 9.3961, "lng": 80.4036, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8]},
    {"name": "Mannar", "province": "Northern", "lat": 8.9810, "lng": 79.9047, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8]},
    {"name": "Vavuniya", "province": "Northern", "lat": 8.7514, "lng": 80.4971, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8]},
    {"name": "Mullaitivu", "province": "Northern", "lat": 9.2671, "lng": 80.8142, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8]},
    {"name": "Batticaloa", "province": "Eastern", "lat": 7.7170, "lng": 81.7000, "climate": ClimateZone.DRY, "peak": [4, 5, 6, 7, 8, 9]},
    {"name": "Ampara", "province": "Eastern", "lat": 7.2916, "lng": 81.6747, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8, 9]},
    {"name": "Trincomalee", "province": "Eastern", "lat": 8.5874, "lng": 81.2152, "climate": ClimateZone.DRY, "peak": [4, 5, 6, 7, 8, 9]},
    {"name": "Kurunegala", "province": "North Western", "lat": 7.4863, "lng": 80.3623, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 7, 8]},
    {"name": "Puttalam", "province": "North Western", "lat": 8.0408, "lng": 79.8394, "climate": ClimateZone.DRY, "peak": [2, 3, 4, 5, 6, 7]},
    {"name": "Anuradhapura", "province": "North Central", "lat": 8.3114, "lng": 80.4037, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8, 9]},
    {"name": "Polonnaruwa", "province": "North Central", "lat": 7.9403, "lng": 81.0188, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8, 9]},
    {"name": "Badulla", "province": "Uva", "lat": 6.9934, "lng": 81.0550, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 4, 8]},
    {"name": "Moneragala", "province": "Uva", "lat": 6.8714, "lng": 81.3506, "climate": ClimateZone.DRY, "peak": [5, 6, 7, 8]},
    {"name": "Ratnapura", "province": "Sabaragamuwa", "lat": 6.6828, "lng": 80.3992, "climate": ClimateZone.WET, "peak": [1, 2, 3, 7, 8]},
    {"name": "Kegalle", "province": "Sabaragamuwa", "lat": 7.2513, "lng": 80.3464, "climate": ClimateZone.INTERMEDIATE, "peak": [1, 2, 3, 7, 8]},
]


PRIORITY_ATTRACTIONS: dict[str, list[dict]] = {
    "Colombo": [
        {"name": "Gangaramaya Temple", "category": AttractionCategory.RELIGIOUS, "fee": 500, "season": [1, 2, 3, 7, 8, 12], "trend": 8.4, "desc": "Eclectic urban temple complex blending Sri Lankan, Thai, Indian and Chinese architecture."},
        {"name": "Galle Face Green", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 7.6, "desc": "A 500-metre seafront promenade beloved for sunset walks, kite-flying and street food."},
        {"name": "National Museum of Colombo", "category": AttractionCategory.CULTURAL, "fee": 1000, "season": list(range(1, 13)), "trend": 6.8, "desc": "The country's largest museum, housing the Kandyan king's regalia and 5,000 years of artifacts."},
        {"name": "Pettah Market", "category": AttractionCategory.FOOD, "fee": 0, "season": list(range(1, 13)), "trend": 7.2, "desc": "Sprawling commercial bazaar with spice, fruit, fabric and electronics streets."},
        {"name": "Dutch Hospital Shopping Precinct", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 7.0, "desc": "Restored 17th-century hospital now hosting cafes, boutiques and rooftop bars."},
        {"name": "Beira Lake", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 6.4, "desc": "Central-city lake with swan boats and the floating Seema Malaka temple."},
        {"name": "Independence Memorial Hall", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 6.6, "desc": "Granite open-air assembly modelled on the Royal Audience Hall of Kandy."},
        {"name": "Viharamahadevi Park", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 6.2, "desc": "Colombo's oldest and largest park, named for the mother of King Dutugamunu."},
        {"name": "Mount Lavinia Beach", "category": AttractionCategory.BEACH, "fee": 0, "season": [11, 12, 1, 2, 3], "trend": 7.4, "desc": "Closest beach resort to Colombo, famed for its colonial-era hotel and seafood Sundays."},
        {"name": "Lotus Tower Observation Deck", "category": AttractionCategory.ADVENTURE, "fee": 2500, "season": list(range(1, 13)), "trend": 8.0, "desc": "South Asia's tallest self-supported tower; observation deck at 350 m gives panoramic city views."},
    ],
    "Kandy": [
        {"name": "Temple of the Sacred Tooth Relic", "category": AttractionCategory.RELIGIOUS, "fee": 1500, "season": list(range(1, 13)), "trend": 9.2, "desc": "Sri Lanka's most venerated Buddhist temple, housing a relic of the Buddha's tooth."},
        {"name": "Royal Botanical Gardens, Peradeniya", "category": AttractionCategory.CULTURAL, "fee": 2500, "season": [1, 2, 3, 7, 8, 9], "trend": 8.4, "desc": "60-hectare 19th-century gardens with the world-renowned Avenue of Royal Palms."},
        {"name": "Kandy Lake", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 7.0, "desc": "Artificial lake built in 1807 by the last king of Kandy, ringed by an easy walking path."},
        {"name": "Bahirawakanda Vihara Buddha Statue", "category": AttractionCategory.RELIGIOUS, "fee": 250, "season": list(range(1, 13)), "trend": 7.2, "desc": "26-metre seated Buddha overlooking Kandy from the western hills."},
        {"name": "Udawatta Kele Forest Reserve", "category": AttractionCategory.WILDLIFE, "fee": 700, "season": [1, 2, 3, 7, 8, 9], "trend": 6.6, "desc": "Royal forest immediately north of the Tooth Temple, home to monkeys, monitor lizards and 80+ bird species."},
        {"name": "Ceylon Tea Museum", "category": AttractionCategory.CULTURAL, "fee": 1000, "season": list(range(1, 13)), "trend": 6.8, "desc": "Hantana hilltop museum tracing the rise of Sri Lanka's signature export."},
        {"name": "Kandyan Cultural Centre Dance Show", "category": AttractionCategory.CULTURAL, "fee": 1500, "season": list(range(1, 13)), "trend": 7.6, "desc": "Nightly showcase of Kandyan dance and traditional drumming."},
        {"name": "Embekka Devalaya", "category": AttractionCategory.RELIGIOUS, "fee": 500, "season": list(range(1, 13)), "trend": 6.4, "desc": "14th-century devale celebrated for the wood-carving virtuosity of its drummers' hall."},
        {"name": "Knuckles Mountain Range", "category": AttractionCategory.ADVENTURE, "fee": 2500, "season": [1, 2, 3, 7, 8], "trend": 8.0, "desc": "UNESCO-listed range offering multi-day treks through cloud forest and montane grassland."},
        {"name": "Esala Perahera Procession Route", "category": AttractionCategory.CULTURAL, "fee": 0, "season": [7, 8], "trend": 8.8, "desc": "Annual 10-night procession of caparisoned elephants and dancers; tickets sell out months ahead."},
    ],
    "Galle": [
        {"name": "Galle Fort", "category": AttractionCategory.CULTURAL, "fee": 0, "season": [11, 12, 1, 2, 3], "trend": 9.0, "desc": "UNESCO-listed Dutch-built fortified old town, walled, livable and impossibly photogenic."},
        {"name": "Galle Lighthouse", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 7.4, "desc": "26-metre lighthouse inside Galle Fort; built by the British in 1939, still operational."},
        {"name": "Jungle Beach", "category": AttractionCategory.BEACH, "fee": 0, "season": [11, 12, 1, 2, 3], "trend": 7.6, "desc": "Sheltered cove a short tuk-tuk from Unawatuna with calm swimming and snorkelling."},
        {"name": "Unawatuna Beach", "category": AttractionCategory.BEACH, "fee": 0, "season": [11, 12, 1, 2, 3], "trend": 8.2, "desc": "Crescent of golden sand and warm shallows; one of the south coast's most loved beaches."},
        {"name": "Sea Turtle Hatchery, Habaraduwa", "category": AttractionCategory.WILDLIFE, "fee": 1000, "season": list(range(1, 13)), "trend": 6.8, "desc": "Conservation centre where injured turtles recover; nightly hatchling releases in season."},
        {"name": "Maritime Archaeology Museum", "category": AttractionCategory.CULTURAL, "fee": 800, "season": list(range(1, 13)), "trend": 6.0, "desc": "Inside a Dutch-era warehouse: shipwreck artifacts and Indian Ocean trade history."},
        {"name": "Japanese Peace Pagoda", "category": AttractionCategory.RELIGIOUS, "fee": 0, "season": list(range(1, 13)), "trend": 6.6, "desc": "White hilltop dagoba with sweeping views over Unawatuna bay."},
        {"name": "Hiyare Reservoir & Rainforest", "category": AttractionCategory.WILDLIFE, "fee": 600, "season": [1, 2, 3, 7, 8], "trend": 6.4, "desc": "Quiet inland reservoir with a research station and easy lakeside trails."},
        {"name": "Kosgoda Beach", "category": AttractionCategory.BEACH, "fee": 0, "season": [11, 12, 1, 2, 3], "trend": 6.8, "desc": "Gold-sand stretch known for the largest concentration of turtle hatcheries on the island."},
        {"name": "Stilt Fishermen of Koggala", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 7.0, "desc": "Iconic stilt-perched fishermen along the Galle-Matara coast; sunrise is the photogenic hour."},
    ],
    "Matale": [
        {"name": "Sigiriya Rock Fortress", "category": AttractionCategory.CULTURAL, "fee": 6000, "season": [1, 2, 3, 5, 6, 7, 8, 9], "trend": 9.6, "desc": "5th-century royal citadel atop a 200-metre granite column; UNESCO World Heritage site."},
        {"name": "Pidurangala Rock", "category": AttractionCategory.ADVENTURE, "fee": 1000, "season": [1, 2, 3, 5, 6, 7, 8, 9], "trend": 8.8, "desc": "Adjacent rock with the iconic sunrise view of Sigiriya from the recumbent Buddha summit."},
        {"name": "Dambulla Cave Temple", "category": AttractionCategory.RELIGIOUS, "fee": 2000, "season": list(range(1, 13)), "trend": 8.4, "desc": "Five painted caves containing 153 statues of the Buddha; oldest murals date to the 1st century BCE."},
        {"name": "Aluvihare Rock Temple", "category": AttractionCategory.RELIGIOUS, "fee": 250, "season": list(range(1, 13)), "trend": 6.6, "desc": "Where the Pali Tipitaka was first transcribed onto ola leaves in the 1st century BCE."},
        {"name": "Spice Garden, Matale", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 6.2, "desc": "Working spice plantation with tasting tours of cinnamon, cardamom and curry leaf."},
        {"name": "Nalanda Gedige", "category": AttractionCategory.CULTURAL, "fee": 500, "season": [1, 2, 3, 7, 8, 9], "trend": 6.0, "desc": "8th-century stone temple combining Hindu and Buddhist motifs; relocated stone-by-stone in the 1980s."},
        {"name": "Sera Ella Falls", "category": AttractionCategory.ADVENTURE, "fee": 200, "season": [1, 2, 3, 4], "trend": 6.4, "desc": "Two-tier waterfall in Knuckles foothills; short forest walk to the base pool."},
        {"name": "Hunas Falls", "category": AttractionCategory.ADVENTURE, "fee": 0, "season": [1, 2, 3, 4, 5], "trend": 6.2, "desc": "75-metre fall in the Knuckles tea country; hotel grounds give the best vantage."},
        {"name": "Riverston Mini World's End", "category": AttractionCategory.ADVENTURE, "fee": 0, "season": [1, 2, 3, 7, 8], "trend": 6.8, "desc": "Cliff-edge plateau in the Knuckles range with a sheer 1,000-metre drop."},
        {"name": "Aukana Buddha Statue", "category": AttractionCategory.RELIGIOUS, "fee": 500, "season": list(range(1, 13)), "trend": 6.6, "desc": "12-metre standing Buddha carved from a single granite outcrop in the 5th century."},
    ],
    "Badulla": [
        {"name": "Ella Rock", "category": AttractionCategory.ADVENTURE, "fee": 0, "season": [1, 2, 3, 7, 8, 9], "trend": 9.0, "desc": "4-hour return hike with sweeping views of Ella Gap; start at sunrise to beat the heat."},
        {"name": "Nine Arches Bridge", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 9.4, "desc": "Iconic 1921 colonial-era stone railway bridge; train passes around 06:30, 09:30, 11:00 and 15:00."},
        {"name": "Little Adam's Peak", "category": AttractionCategory.ADVENTURE, "fee": 0, "season": [1, 2, 3, 7, 8, 9], "trend": 8.4, "desc": "Easy 45-minute climb with classic Hill Country views; great for sunrise or sunset."},
        {"name": "Ravana Falls", "category": AttractionCategory.ADVENTURE, "fee": 200, "season": [10, 11, 12, 1, 2], "trend": 7.8, "desc": "25-metre roadside waterfall named after the Ramayana king who allegedly hid Sita in nearby caves."},
        {"name": "Demodara Loop", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 6.8, "desc": "Engineering marvel where the railway loops over itself to gain elevation."},
        {"name": "Lipton's Seat", "category": AttractionCategory.CULTURAL, "fee": 0, "season": [1, 2, 3, 7, 8], "trend": 7.4, "desc": "Hilltop viewpoint where Sir Thomas Lipton surveyed his tea empire; reach it before 09:00 for clear views."},
        {"name": "Dunhinda Falls", "category": AttractionCategory.ADVENTURE, "fee": 100, "season": [10, 11, 12, 1, 2], "trend": 7.0, "desc": "63-metre fall reached via a one-kilometre forest path from Badulla."},
        {"name": "Diyaluma Falls", "category": AttractionCategory.ADVENTURE, "fee": 0, "season": [10, 11, 12, 1, 2], "trend": 7.6, "desc": "220-metre cascade — the country's second-tallest — with infinity-pool plunge pools at the top."},
        {"name": "Bogoda Wooden Bridge", "category": AttractionCategory.CULTURAL, "fee": 0, "season": list(range(1, 13)), "trend": 6.2, "desc": "16th-century wooden bridge with shingled roof; one of the oldest of its kind in Asia."},
        {"name": "Muthiyangana Raja Maha Vihara", "category": AttractionCategory.RELIGIOUS, "fee": 0, "season": list(range(1, 13)), "trend": 6.4, "desc": "Ancient temple in central Badulla, said to mark a visit by the Buddha himself."},
    ],
}

# Lightweight stubs (non-priority districts) — 3 each, generic but plausible.
SECONDARY_TEMPLATES: list[dict] = [
    {"suffix": "Beach", "category": AttractionCategory.BEACH, "trend": 5.5},
    {"suffix": "Temple", "category": AttractionCategory.RELIGIOUS, "trend": 5.4},
    {"suffix": "Heritage Site", "category": AttractionCategory.CULTURAL, "trend": 5.6},
]


class Command(BaseCommand):
    help = (
        "Seed districts (25) and a starter set of attractions. "
        "Idempotent unless --flush is supplied."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all existing districts/attractions before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["flush"]:
            Attraction.objects.all().delete()
            District.objects.all().delete()
            self.stdout.write(self.style.WARNING("Flushed districts + attractions."))

        district_lookup: dict[str, District] = {}
        for d in DISTRICTS:
            obj, created = District.objects.update_or_create(
                name=d["name"],
                defaults={
                    "province": d["province"],
                    "lat": d["lat"],
                    "lng": d["lng"],
                    "climate_zone": d["climate"],
                    "peak_months": d["peak"],
                    "description": (
                        f"{d['name']} is one of the {d['province']} Province "
                        f"districts of Sri Lanka."
                    ),
                },
            )
            district_lookup[d["name"]] = obj
            self.stdout.write(
                ("+ " if created else "  ") + f"district: {d['name']} ({d['province']})"
            )

        # Priority attractions
        attraction_count = 0
        for district_name, attractions in PRIORITY_ATTRACTIONS.items():
            district = district_lookup[district_name]
            for a in attractions:
                slug = slugify(f"{a['name']}-{district_name}")
                _, created = Attraction.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "district": district,
                        "name": a["name"],
                        "category": a["category"],
                        "description": a["desc"],
                        "address": district_name,
                        "lat": district.lat,
                        "lng": district.lng,
                        "entry_fee_lkr": a["fee"],
                        "best_season": a["season"],
                        "crowd_index": min(10, max(1, int(a["trend"]))),
                        "trend_score": a["trend"],
                    },
                )
                if created:
                    attraction_count += 1

        # Secondary stubs
        secondary_districts = [
            d for d in DISTRICTS if d["name"] not in PRIORITY_ATTRACTIONS
        ]
        for d in secondary_districts:
            district = district_lookup[d["name"]]
            for tpl in SECONDARY_TEMPLATES:
                name = f"{d['name']} {tpl['suffix']}"
                slug = slugify(name)
                _, created = Attraction.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "district": district,
                        "name": name,
                        "category": tpl["category"],
                        "description": (
                            f"Representative {tpl['category']} attraction in "
                            f"{d['name']} ({d['province']} Province)."
                        ),
                        "address": d["name"],
                        "lat": d["lat"],
                        "lng": d["lng"],
                        "entry_fee_lkr": 0,
                        "best_season": d["peak"],
                        "crowd_index": 4,
                        "trend_score": tpl["trend"],
                    },
                )
                if created:
                    attraction_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {District.objects.count()} districts, "
                f"{Attraction.objects.count()} attractions "
                f"({attraction_count} new this run)."
            )
        )
