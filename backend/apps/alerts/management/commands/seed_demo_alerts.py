"""Create sample SafetyAlert rows for local demo / empty databases."""

from django.core.management.base import BaseCommand

from apps.alerts.models import SafetyAlert
from apps.attractions.models import District

DEMO_SOURCE = "LankaGuide (demo seed)"


class Command(BaseCommand):
    help = "Insert demo travel advisories (use --replace to refresh demo rows)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Add demo rows even when other non-demo active alerts already exist.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing demo-seeded rows (same source_name) then add fresh ones.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        replace = options["replace"]

        if replace:
            deleted, _ = SafetyAlert.objects.filter(source_name=DEMO_SOURCE).delete()
            if deleted:
                self.stdout.write(f"Removed {deleted} previous demo row(s).")

        if SafetyAlert.objects.filter(source_name=DEMO_SOURCE).exists():
            self.stdout.write(
                self.style.WARNING(
                    "Demo advisories already exist. Pass --replace to delete and recreate them."
                )
            )
            return

        other_active = (
            SafetyAlert.objects.filter(active=True)
            .exclude(source_name=DEMO_SOURCE)
            .exists()
        )
        if other_active and not force:
            self.stdout.write(
                self.style.WARNING(
                    "Active non-demo alerts exist. Pass --force to add demo rows as well, "
                    "or use an empty database / deactivate other alerts first."
                )
            )
            return

        colombo = District.objects.filter(name__iexact="Colombo").first()
        kandy = District.objects.filter(name__iexact="Kandy").first()

        samples = [
            {
                "district": colombo,
                "title": "High humidity and afternoon showers",
                "body": (
                    "Brief thunderstorms are common in the west during this season. "
                    "Carry water, plan indoor or morning outdoor blocks, and allow "
                    "extra time for traffic in the capital."
                ),
                "severity": SafetyAlert.Severity.INFO,
                "source_url": "https://open-meteo.com/",
                "source_name": DEMO_SOURCE,
            },
            {
                "district": kandy,
                "title": "Hill country: cooler evenings",
                "body": (
                    "Temperatures drop after sunset in the central highlands. "
                    "Pack a light layer for temples and evening walks."
                ),
                "severity": SafetyAlert.Severity.WARNING,
                "source_url": "",
                "source_name": DEMO_SOURCE,
            },
            {
                "district": None,
                "title": "General travel awareness",
                "body": (
                    "Stay on marked trails at heritage sites, hydrate often, and "
                    "check local notices before long inter-city road trips."
                ),
                "severity": SafetyAlert.Severity.INFO,
                "source_url": "",
                "source_name": DEMO_SOURCE,
            },
        ]

        created = 0
        for row in samples:
            obj = SafetyAlert.objects.create(**row)
            created += 1
            self.stdout.write(f"  + [{obj.severity}] {obj.title[:50]}…")

        self.stdout.write(self.style.SUCCESS(f"Created {created} demo advisory(ies)."))
