"""
Itinerary service lives in `lankaguide.services.itinerary_service` (RAG + Gemini).

This module re-exports the class so existing imports keep working:
`from apps.itinerary.services import ItineraryService`
"""

from __future__ import annotations

from lankaguide.services.itinerary_service import ItineraryService

__all__ = ["ItineraryService"]
