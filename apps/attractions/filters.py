"""
Lightweight filtering helpers for the attractions ViewSet.

Implements the filter contract from PRD §8.2:
    GET /api/v1/attractions/?district_id=&category=&season=

Hand-rolled (no `django-filter` dep) so the project keeps a minimal install
footprint. Each helper accepts a queryset + a request and returns a
queryset narrowed by recognised query parameters.
"""

from __future__ import annotations

from django.db.models import QuerySet

from .models import Attraction


def filter_attractions(qs: QuerySet[Attraction], request) -> QuerySet[Attraction]:
    params = request.query_params

    district_id = params.get("district_id") or params.get("district")
    if district_id and district_id.isdigit():
        qs = qs.filter(district_id=int(district_id))

    category = params.get("category")
    if category:
        qs = qs.filter(category=category)

    season = params.get("season")
    if season and season.isdigit():
        # `best_season` is a JSON list of month numbers — match if month is in.
        qs = qs.filter(best_season__contains=int(season))

    search = params.get("q") or params.get("search")
    if search:
        qs = qs.filter(name__icontains=search)

    return qs
