"""
ItineraryService — generates a day-by-day itinerary as structured JSON.

Strategy:
1. Fetch attraction context from the relational pool filtered by user interests.
2. Build the itinerary prompt with seasonal context.
3. Call Gemini Pro with `response_mime_type="application/json"`.
4. Parse the JSON, persist to the relational store, return the freshly-saved
   Itinerary instance.

If Gemini cannot produce a usable plan after retries, this service raises
a RuntimeError. The view turns that into a 503 — there is no fake fallback.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

from django.conf import settings
from django.db import transaction

from django.contrib.auth import get_user_model

from apps.attractions.models import Attraction, District
from apps.core.services.embeddings import get_embedding_client
from apps.core.services.vectorstore import get_collection
from apps.itinerary.models import (
    Itinerary,
    ItineraryDay,
    ItineraryStatus,
    ItineraryStop,
)

User = get_user_model()

logger = logging.getLogger("lankaguide.itinerary.service")

ITINERARY_SYSTEM = """\
You are a Sri Lanka travel planning expert.
Generate a day-by-day itinerary as valid JSON matching the schema provided.
Use ONLY attractions mentioned in the CONTEXT below.
Respect the user's budget, interests, group type, and travel dates.
Factor in the seasonal data provided: avoid flooded roads and monsoon-heavy areas.
Output ONLY the JSON object. No additional commentary.
"""

OUTPUT_SCHEMA = """\
{
  "title": str,
  "days": [
    {
      "day": int (1-based),
      "district": str,
      "notes": str,
      "stops": [
        {
          "attraction_id": int,
          "name": str,
          "arrival_time": "HH:MM",
          "duration_mins": int,
          "tip": str
        }
      ]
    }
  ]
}
"""

MAX_OUTPUT_TOKENS = 2048  # PRD §9.6


# ───────────────────────── Helpers ─────────────────────────────────────
@dataclass
class AttractionContext:
    id: int
    name: str
    slug: str
    district_id: int
    district_name: str
    category: str
    crowd_index: int
    trend_score: float
    description: str

    def as_prompt_line(self) -> str:
        return (
            f"- id={self.id} | {self.name} ({self.district_name}, "
            f"{self.category}, crowd={self.crowd_index}) — {self.description[:160]}"
        )


@dataclass
class DistrictSeasonContext:
    id: int
    name: str
    climate_zone: str
    peak_months: list[int]

    def as_prompt_line(self) -> str:
        return (
            f"- {self.name} (id={self.id}, climate={self.climate_zone}, "
            f"peak_months={self.peak_months})"
        )


def _build_attraction_pool(
    interests: list[str], district_ids: list[int], limit: int = 60
) -> list[AttractionContext]:
    qs = (
        Attraction.objects.filter(
            district_id__in=district_ids, category__in=interests
        )
        .select_related("district")
        .order_by("-trend_score")[:limit]
    )
    return [
        AttractionContext(
            id=a.id,
            name=a.name,
            slug=a.slug,
            district_id=a.district_id,
            district_name=a.district.name,
            category=a.category,
            crowd_index=a.crowd_index,
            trend_score=a.trend_score,
            description=a.description,
        )
        for a in qs
    ]


def _district_season_context(district_ids: list[int]) -> list[DistrictSeasonContext]:
    qs = District.objects.filter(id__in=district_ids)
    return [
        DistrictSeasonContext(
            id=d.id,
            name=d.name,
            climate_zone=d.climate_zone,
            peak_months=list(d.peak_months or []),
        )
        for d in qs
    ]


def _retrieve_chunks_for(
    interests: list[str], district_ids: list[int], k: int = 6
) -> list[dict]:
    """Best-effort RAG seed text filtered by selected metadata."""
    try:
        embed = get_embedding_client()
        collection = get_collection()
        question = (
            "Plan a trip in Sri Lanka covering "
            + ", ".join(interests)
            + " activities across districts: "
            + ", ".join(map(str, district_ids))
        )
        embedding = embed.embed(question, purpose="query")
        collected: list[dict] = []
        seen_keys: set[str] = set()

        where = {
            "$and": [
                {"district_id": {"$in": district_ids}},
                {"category": {"$in": interests}},
            ]
        }
        result = collection.query(
            query_embeddings=[embedding], n_results=k, where=where
        )
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        for doc, meta in zip(docs, metas):
            if not doc:
                continue
            meta = meta or {}
            key = (
                f"{meta.get('attraction_id')}::{meta.get('chunk_index')}::"
                f"{meta.get('slug')}"
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            collected.append({"text": doc, "meta": meta})

        # Fallback fill if strict metadata query is sparse.
        if len(collected) < k:
            fill = collection.query(query_embeddings=[embedding], n_results=max(k, 10))
            fill_docs = (fill.get("documents") or [[]])[0]
            fill_metas = (fill.get("metadatas") or [[]])[0]
            for doc, meta in zip(fill_docs, fill_metas):
                if not doc:
                    continue
                meta = meta or {}
                key = (
                    f"{meta.get('attraction_id')}::{meta.get('chunk_index')}::"
                    f"{meta.get('slug')}"
                )
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                collected.append({"text": doc, "meta": meta})
                if len(collected) >= k:
                    break
        return collected[:k]
    except Exception as exc:  # noqa: BLE001
        logger.debug("Knowledge-base retrieval skipped: %s", exc)
        return []


# ───────────────────────── Service ─────────────────────────────────────
class ItineraryService:
    def __init__(self, gemini_client: Any | None = None):
        self._gemini_model = settings.GEMINI_PRO_MODEL
        self._fallback_model = settings.GEMINI_CHAT_MODEL
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. The itinerary planner is unavailable."
            )
        if gemini_client is not None:
            self._gemini = gemini_client
        else:
            try:
                import google.generativeai as genai

                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._gemini = genai.GenerativeModel(self._gemini_model)
                self._gemini_fallback = (
                    genai.GenerativeModel(self._fallback_model)
                    if self._fallback_model and self._fallback_model != self._gemini_model
                    else None
                )
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    f"Failed to initialise Gemini for itinerary: {exc}"
                ) from exc

    # ─────────────────── Public API ────────────────────────────────────
    @transaction.atomic
    def generate(self, *, user, preferences: dict) -> Itinerary:
        pool = _build_attraction_pool(
            interests=preferences["interests"],
            district_ids=preferences["district_ids"],
        )
        if not pool:
            raise RuntimeError(
                "No attractions match the requested districts/interests. "
                "Run `python manage.py seed_database` first."
            )
        seasons = _district_season_context(preferences["district_ids"])
        chunks = _retrieve_chunks_for(
            preferences["interests"], preferences["district_ids"]
        )

        plan_dict: dict | None = None
        if self._gemini is not None:
            plan_dict = self._call_gemini(
                pool=pool,
                seasons=seasons,
                chunks=chunks,
                preferences=preferences,
            )

        if plan_dict is None:
            raise RuntimeError(
                "AI planner is currently unavailable (model/quota issue). "
                "Please retry in a few minutes."
            )
        plan_dict = self._normalize_plan(
            plan=plan_dict,
            pool=pool,
            preferences=preferences,
        )

        return self._persist(user=user, preferences=preferences, plan=plan_dict)

    @transaction.atomic
    def regenerate_day(self, *, itinerary: Itinerary, day_number: int) -> ItineraryDay:
        """
        Regenerates a single day. Convenience method for the
        `PATCH /api/v1/itinerary/{id}/day/{n}/regenerate/` endpoint (PRD §8.2).
        """
        try:
            day = itinerary.days.get(day_number=day_number)
        except ItineraryDay.DoesNotExist as exc:
            raise ValueError(
                f"Day {day_number} not found on itinerary {itinerary.id}"
            ) from exc

        existing_district_ids = list(
            itinerary.days.values_list("district_id", flat=True)
        )
        all_districts = [d for d in existing_district_ids if d] or [day.district_id]
        pool = _build_attraction_pool(
            interests=[s.attraction.category for s in day.stops.all()] or ["cultural"],
            district_ids=all_districts,
        )
        if not pool:
            return day

        # Pick three lowest-trend-score attractions to ensure variety vs. existing.
        used_ids = set(
            ItineraryStop.objects.filter(day__itinerary=itinerary).values_list(
                "attraction_id", flat=True
            )
        )
        fresh = [a for a in pool if a.id not in used_ids][:3] or pool[:3]

        ItineraryStop.objects.filter(day=day).delete()
        for order, att in enumerate(fresh, start=1):
            ItineraryStop.objects.create(
                day=day,
                attraction_id=att.id,
                stop_order=order,
                duration_mins=120,
                tip="Regenerated suggestion — confirm opening hours.",
            )
        day.notes = "Day regenerated from updated preferences."
        day.save(update_fields=["notes"])
        return day

    # ─────────────────── Gemini call ───────────────────────────────────
    def _build_prompt(
        self,
        *,
        pool: list[AttractionContext],
        seasons: list[DistrictSeasonContext],
        chunks: list[dict],
        preferences: dict,
    ) -> str:
        sections: list[str] = [ITINERARY_SYSTEM, "OUTPUT_SCHEMA:", OUTPUT_SCHEMA]
        sections += [
            "USER PREFERENCES:",
            json.dumps(
                {
                    "start_date": str(preferences["start_date"]),
                    "end_date": str(preferences["end_date"]),
                    "num_days": preferences["num_days"],
                    "budget_lkr": str(preferences["budget_lkr"]),
                    "interests": preferences["interests"],
                    "group_type": preferences["group_type"],
                    "group_size": preferences["group_size"],
                    "district_ids": preferences["district_ids"],
                },
                indent=2,
            ),
        ]
        sections += ["DISTRICT SEASONAL CONTEXT:"]
        sections += [s.as_prompt_line() for s in seasons]
        sections += ["", "ATTRACTION CONTEXT (use ONLY these — refer by id):"]
        sections += [a.as_prompt_line() for a in pool]
        if chunks:
            sections += ["", "RELEVANT KNOWLEDGE EXTRACTS:"]
            sections += [
                f"- ({c['meta'].get('slug', '?')}) {c['text'][:400]}" for c in chunks
            ]
        sections += ["", "Output the JSON object now."]
        return "\n".join(sections)

    def _call_gemini(
        self,
        *,
        pool: list[AttractionContext],
        seasons: list[DistrictSeasonContext],
        chunks: list[dict],
        preferences: dict,
    ) -> dict | None:
        prompt = self._build_prompt(
            pool=pool, seasons=seasons, chunks=chunks, preferences=preferences
        )
        models_to_try = [self._gemini]
        if getattr(self, "_gemini_fallback", None) is not None:
            models_to_try.append(self._gemini_fallback)

        attempt = 0
        delay = 1.0
        while attempt < 3:
            for model in models_to_try:
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "max_output_tokens": MAX_OUTPUT_TOKENS,
                            "temperature": 0.5,
                            "top_p": 0.95,
                            "response_mime_type": "application/json",
                        },
                    )
                    text = (getattr(response, "text", "") or "").strip()
                    if not text:
                        text = self._extract_text_from_response(response).strip()
                    if text:
                        parsed = self._parse_json(text, pool)
                        if parsed is not None:
                            return parsed
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Itinerary Gemini call failed (attempt %s/3, model=%s): %s",
                        attempt + 1,
                        getattr(model, "model_name", "unknown"),
                        exc,
                    )
            time.sleep(delay)
            delay = min(delay * 2, 20)
            attempt += 1
        return None

    @staticmethod
    def _extract_text_from_response(response: Any) -> str:
        """Extract text when SDK does not populate `response.text`."""
        candidates = getattr(response, "candidates", None) or []
        out: list[str] = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                text = getattr(part, "text", None)
                if text:
                    out.append(text)
        return "\n".join(out)

    @staticmethod
    def _parse_json(raw: str, pool: list[AttractionContext]) -> dict | None:
        # Strip markdown fences if any leaked through despite mime_type.
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning("Itinerary JSON parse failed: %s", exc)
            return None

        # Sanity: only allow attractions that exist in our pool.
        valid_ids = {a.id for a in pool}
        for day in data.get("days", []):
            day["stops"] = [
                s
                for s in day.get("stops", [])
                if isinstance(s.get("attraction_id"), int)
                and s["attraction_id"] in valid_ids
            ]
        if not data.get("days"):
            return None
        return data

    @staticmethod
    def _normalize_plan(
        *, plan: dict, pool: list[AttractionContext], preferences: dict
    ) -> dict:
        """Normalize AI output to avoid repeated/invalid day plans."""
        num_days = int(preferences["num_days"])
        district_ids = list(preferences["district_ids"])
        by_id = {a.id: a for a in pool}
        by_district: dict[int, list[int]] = {}
        for attraction in pool:
            by_district.setdefault(attraction.district_id, []).append(attraction.id)

        input_days = plan.get("days") or []
        normalized_days: list[dict] = []
        used_global: set[int] = set()

        # Build exactly N days; synthesize missing ones deterministically.
        for i in range(num_days):
            src = input_days[i] if i < len(input_days) else {}
            day_number = i + 1
            district_id = src.get("district_id")
            if not district_id and district_ids:
                district_id = district_ids[i % len(district_ids)]

            candidate_pool = by_district.get(district_id) or list(by_id.keys())
            day_stops: list[dict] = []
            day_seen: set[int] = set()

            # Pass 1: keep AI-suggested stops but remove duplicates.
            for stop in src.get("stops") or []:
                attraction_id = stop.get("attraction_id")
                if not isinstance(attraction_id, int):
                    continue
                if attraction_id not in by_id:
                    continue
                if attraction_id in day_seen or attraction_id in used_global:
                    continue
                day_seen.add(attraction_id)
                used_global.add(attraction_id)
                day_stops.append(stop)
                if len(day_stops) >= 4:
                    break

            # Pass 2: fill from district pool, then global pool.
            if len(day_stops) < 3:
                fill_order = candidate_pool + [aid for aid in by_id if aid not in candidate_pool]
                for attraction_id in fill_order:
                    if attraction_id in day_seen or attraction_id in used_global:
                        continue
                    day_seen.add(attraction_id)
                    used_global.add(attraction_id)
                    att = by_id[attraction_id]
                    day_stops.append(
                        {
                            "attraction_id": attraction_id,
                            "name": att.name,
                            "duration_mins": 120,
                            "tip": "Added to diversify the plan across days.",
                        }
                    )
                    if len(day_stops) >= 3:
                        break

            # Last resort for very small datasets.
            if len(day_stops) < 1 and candidate_pool:
                attraction_id = candidate_pool[i % len(candidate_pool)]
                att = by_id[attraction_id]
                day_stops.append(
                    {
                        "attraction_id": attraction_id,
                        "name": att.name,
                        "duration_mins": 120,
                        "tip": "Limited dataset; repeated attraction.",
                    }
                )

            # Standardize stop fields and timing.
            cleaned_stops: list[dict] = []
            for order, stop in enumerate(day_stops, start=1):
                attraction_id = stop["attraction_id"]
                cleaned_stops.append(
                    {
                        "attraction_id": attraction_id,
                        "name": stop.get("name") or by_id[attraction_id].name,
                        "stop_order": order,
                        "arrival_time": stop.get("arrival_time") or _suggested_time(order - 1),
                        "duration_mins": int(stop.get("duration_mins") or 120),
                        "tip": stop.get("tip") or "Best visited during daylight hours.",
                    }
                )

            normalized_days.append(
                {
                    "day": day_number,
                    "district_id": district_id,
                    "notes": src.get("notes") or "AI optimized route for this day.",
                    "stops": cleaned_stops,
                }
            )

        plan["days"] = normalized_days
        plan["title"] = plan.get("title") or f"{num_days}-Day Sri Lanka Trip"
        return plan

    # ─────────────────── Persistence ───────────────────────────────────
    @staticmethod
    def _persist(
        *, user, preferences: dict, plan: dict
    ) -> Itinerary:
        itinerary = Itinerary.objects.create(
            user=user,
            title=plan.get("title")
            or preferences.get("title")
            or f"{preferences['num_days']}-Day Sri Lanka Trip",
            start_date=preferences["start_date"],
            end_date=preferences["end_date"],
            budget_lkr=preferences["budget_lkr"],
            group_type=preferences["group_type"],
            group_size=preferences["group_size"],
            status=ItineraryStatus.DRAFT,
        )

        for raw_day in plan.get("days", []):
            district_id = raw_day.get("district_id")
            if not district_id:
                first_stop = (raw_day.get("stops") or [{}])[0]
                attraction_id = first_stop.get("attraction_id")
                if attraction_id:
                    district_id = (
                        Attraction.objects.filter(id=attraction_id)
                        .values_list("district_id", flat=True)
                        .first()
                    )

            day = ItineraryDay.objects.create(
                itinerary=itinerary,
                day_number=int(raw_day.get("day") or 0),
                district_id=district_id,
                notes=raw_day.get("notes", ""),
                ai_generated=True,
            )
            for order, stop in enumerate(raw_day.get("stops") or [], start=1):
                attraction_id = stop.get("attraction_id")
                if not attraction_id:
                    continue
                ItineraryStop.objects.create(
                    day=day,
                    attraction_id=attraction_id,
                    stop_order=int(stop.get("stop_order") or order),
                    arrival_time=_parse_time(stop.get("arrival_time")),
                    duration_mins=stop.get("duration_mins"),
                    tip=stop.get("tip", ""),
                )
        return itinerary


# ───────────────────────── Misc helpers ────────────────────────────────
_TIMES = ["09:00", "11:30", "14:30", "17:00"]


def _suggested_time(idx: int) -> str:
    return _TIMES[min(idx, len(_TIMES) - 1)]


def _parse_time(value: Any):
    from datetime import time as _t

    if value is None:
        return None
    if isinstance(value, str):
        try:
            hh, mm = value.split(":")[:2]
            return _t(int(hh), int(mm))
        except Exception:
            return None
    return None
