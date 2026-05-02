"""`GET /api/v1/routing/eta/?from=lat,lng&to=lat,lng` (or via attraction ids)."""

from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attractions.models import Attraction, District

from .services import get_route


def _resolve_pair(qs_value: str) -> tuple[float | None, float | None, str | None]:
    if not qs_value:
        return None, None, None
    if "," in qs_value:
        try:
            lat, lng = [float(p.strip()) for p in qs_value.split(",")[:2]]
            return lat, lng, None
        except ValueError:
            return None, None, None
    return None, None, None


class EtaView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        f = request.query_params.get("from") or ""
        t = request.query_params.get("to") or ""
        from_attraction = request.query_params.get("from_attraction")
        to_attraction = request.query_params.get("to_attraction")
        from_district = request.query_params.get("from_district")
        to_district = request.query_params.get("to_district")

        from_lat, from_lng, district_a = _resolve_pair(f)
        to_lat, to_lng, district_b = _resolve_pair(t)

        if from_attraction:
            a = self._attraction(from_attraction)
            if a:
                from_lat, from_lng = float(a.lat or 0), float(a.lng or 0)
                district_a = a.district.name
        if to_attraction:
            a = self._attraction(to_attraction)
            if a:
                to_lat, to_lng = float(a.lat or 0), float(a.lng or 0)
                district_b = a.district.name
        if from_district:
            d = self._district(from_district)
            if d:
                from_lat, from_lng = float(d.lat or 0), float(d.lng or 0)
                district_a = d.name
        if to_district:
            d = self._district(to_district)
            if d:
                to_lat, to_lng = float(d.lat or 0), float(d.lng or 0)
                district_b = d.name

        if not all([from_lat, from_lng, to_lat, to_lng]):
            return Response(
                {"detail": "Provide from & to as 'lat,lng' or use attraction/district ids."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = get_route(
            from_lat, from_lng, to_lat, to_lng,
            district_a=district_a, district_b=district_b,
        )
        if result is None:
            return Response(
                {
                    "detail": "Routing service is unavailable right now.",
                    "code": "routing_unavailable",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(result)

    @staticmethod
    def _attraction(value: str):
        try:
            return Attraction.objects.select_related("district").get(pk=int(value))
        except (Attraction.DoesNotExist, ValueError):
            try:
                return Attraction.objects.select_related("district").get(slug=value)
            except Attraction.DoesNotExist:
                return None

    @staticmethod
    def _district(value: str):
        try:
            return District.objects.get(pk=int(value))
        except (District.DoesNotExist, ValueError):
            try:
                return District.objects.get(slug=value)
            except District.DoesNotExist:
                try:
                    return District.objects.get(name__iexact=value)
                except District.DoesNotExist:
                    return None
