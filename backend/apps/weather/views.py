"""`GET /api/v1/weather/?district_id=...` or `?lat=&lng=`."""

from __future__ import annotations

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.attractions.models import District

from .services import fetch_current, fetch_forecast


class WeatherView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        district_id = request.query_params.get("district_id")
        if district_id:
            try:
                d = District.objects.get(pk=int(district_id))
            except (District.DoesNotExist, ValueError):
                return Response(
                    {"detail": "District not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            if not d.lat or not d.lng:
                return Response(
                    {"detail": "District has no coordinates."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            lat, lng = float(d.lat), float(d.lng)

        try:
            lat, lng = float(lat), float(lng)
        except (TypeError, ValueError):
            return Response(
                {"detail": "Provide either district_id, or lat & lng."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        current = fetch_current(lat, lng)
        if current is None:
            return Response(
                {
                    "detail": (
                        "Weather could not be loaded (Open-Meteo and OpenWeatherMap "
                        "both failed). Check your network or try again later."
                    ),
                    "code": "weather_unavailable",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        forecast = fetch_forecast(lat, lng) or []
        return Response({"current": current, "forecast": forecast})
