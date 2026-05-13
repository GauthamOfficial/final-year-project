"""Batch-compute attraction sentiment (OSM/Nominatim + Wikipedia + HF + Gemini)."""

from __future__ import annotations

import time

from django.core.management.base import BaseCommand, CommandError

from lankaguide.services.sentiment_service import SentimentService

from ...models import Attraction


class Command(BaseCommand):
    help = "Resolve open text via OSM/Wikipedia and persist sentiment fields on Attraction rows."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "--attraction_id",
            type=int,
            help="Compute sentiment for a single attraction primary key.",
        )
        group.add_argument(
            "--all",
            action="store_true",
            help="Compute sentiment for every attraction (1s pause between rows).",
        )

    def handle(self, *args, **options):
        service = SentimentService()
        if options.get("attraction_id") is not None:
            aid = options["attraction_id"]
            name = (
                Attraction.objects.filter(pk=aid)
                .values_list("name", flat=True)
                .first()
            )
            self.stdout.write(
                f"Computing sentiment for {name or '?'} (id={aid})…",
                ending=" ",
            )
            self._one(service, aid, inline=True)
            self.stdout.write("")
            return

        rows = list(Attraction.objects.order_by("id").values_list("id", "name"))
        self.stdout.write(f"Processing {len(rows)} attractions…")
        for i, (aid, name) in enumerate(rows, start=1):
            self.stdout.write(
                f"[{i}/{len(rows)}] {name} (id={aid}) …",
                ending=" ",
            )
            self._one(service, aid, inline=True)
            self.stdout.write("")
            if i < len(rows):
                time.sleep(1)

    def _one(
        self,
        service: SentimentService,
        attraction_id: int,
        *,
        inline: bool = False,
    ):
        try:
            result = service.compute_attraction_sentiment(attraction_id)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(f"error: {exc}"))
            return

        if result.get("error") == "no open text sources found":
            self.stdout.write(self.style.WARNING("no open text sources found"))
            return

        if inline:
            self.stdout.write(
                self.style.SUCCESS(
                    f"ok · {result.get('sentiment_label')} "
                    f"score={result.get('sentiment_score')} "
                    f"+{result.get('positive_pct')}%"
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("Success"))
            self.stdout.write(
                f"  label={result.get('sentiment_label')} "
                f"score={result.get('sentiment_score')} "
                f"positive_pct={result.get('positive_pct')}"
            )
