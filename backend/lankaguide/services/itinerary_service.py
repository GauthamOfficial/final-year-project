"""
Itinerary generation via **Retrieval-Augmented Generation** (Gap — academic RAG claim).

Pipeline:
1. **ChromaDB** semantic search (Gemini embeddings via `get_embedding_client`).
2. MySQL **district / seasonal / top attractions** context.
3. Structured **multi-section prompt** to **Gemini 1.5 Pro** (`application/json`).
4. Persist itinerary with **RAG audit** metadata (`rag_used`, `retrieved_doc_ids`).

Embeddings follow the project default (`GEMINI_EMBEDDING_MODEL`, typically
`gemini-embedding-001`) — not the older `text-embedding-004` name, but the
retrieval step is still RAG: vector store query → context injection → LLM.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.attractions.models import Attraction, District, SeasonalData
from apps.core.services.embeddings import get_embedding_client
from apps.core.services.vectorstore import get_collection
from apps.itinerary.models import (
    Itinerary,
    ItineraryDay,
    ItineraryStatus,
    ItineraryStop,
)

User = get_user_model()
logger = logging.getLogger("lankaguide.itinerary.rag")

MAX_OUTPUT_TOKENS = 4096

ITINERARY_SYSTEM = """
You are a Sri Lanka travel planning expert.
Generate a day-by-day itinerary as valid JSON matching the schema provided below.
Use ONLY attractions, places and facts mentioned in the RETRIEVED KNOWLEDGE section.
Respect the user's budget, interests, group type, and travel dates.
Factor in the seasonal notes provided — avoid flooding-prone areas during monsoon months.

CRITICAL multi-day rules (never violate these):
- The "days" array MUST contain exactly the requested number of day objects,
  numbered 1 through N with no gaps and no duplicate day numbers.
- Each day MUST visit different attractions — the same place must NOT appear
  on more than one day.
- Each day MUST have a distinct theme, district focus, and schedule. Never
  copy Day 1's stops onto Day 2 or later days.
- Spread the trip across the selected districts in a logical geographic order.

Output ONLY a valid JSON object. No markdown, no explanation, no commentary outside JSON.
""".strip()

SINGLE_DAY_SCHEMA_BLOCK = """
=== OUTPUT JSON SCHEMA (single day only) ===
{{
  "days": [
    {{
      "day": {day_number},
      "district": "string",
      "theme": "string — one-line day theme",
      "stops": [
        {{
          "name": "string — attraction name",
          "arrival_time": "HH:MM",
          "duration_mins": 90,
          "description": "string — 1-2 sentences why this fits the user",
          "tip": "string — practical visitor tip"
        }}
      ],
      "accommodation_note": "string — brief advice on where to stay"
    }}
  ]
}}
=== END SCHEMA ===
""".strip()

OUTPUT_SCHEMA_BLOCK = """
=== OUTPUT JSON SCHEMA ===
{
  "title": "string — trip title",
  "days": [
    {
      "day": 1,
      "district": "string",
      "theme": "string — one-line day theme",
      "stops": [
        {
          "name": "string — attraction name",
          "arrival_time": "HH:MM",
          "duration_mins": 90,
          "description": "string — 1-2 sentences why this fits the user",
          "tip": "string — practical visitor tip"
        }
      ],
      "accommodation_note": "string — brief advice on where to stay"
    }
  ],
  "budget_note": "string — brief note on estimated daily cost",
  "best_transport": "string — recommended transport between stops"
}
=== END SCHEMA ===
""".strip()


# ───────────────────────── Data containers ─────────────────────────────
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

    def as_hint_line(self) -> str:
        return (
            f"- attraction_id={self.id} | {self.name} | district={self.district_name} | "
            f"{self.category} | crowd_index={self.crowd_index}"
        )


@dataclass
class DistrictSeasonContext:
    id: int
    name: str
    climate_zone: str
    peak_months: list[int]

    def as_prompt_line(self) -> str:
        return (
            f"- {self.name} (district_id={self.id}, climate={self.climate_zone}, "
            f"peak_months={self.peak_months})"
        )


# ───────────────────────── MySQL + RAG helpers ───────────────────────
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
            description=a.description or "",
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


def _district_name_list(district_ids: list[int]) -> str:
    names = list(
        District.objects.filter(id__in=district_ids)
        .order_by("name")
        .values_list("name", flat=True)
    )
    return ", ".join(names)


def _top_attractions_hints(district_ids: list[int], n: int = 3) -> str:
    lines: list[str] = []
    for did in district_ids:
        qs = (
            Attraction.objects.filter(district_id=did)
            .select_related("district")
            .order_by("-trend_score")[:n]
        )
        for a in qs:
            lines.append(
                f"- attraction_id={a.id} | {a.name} | {a.district.name} | {a.category}"
            )
    return "\n".join(lines) if lines else "(no attractions in selected districts)"


def _seasonal_window_notes(
    district_ids: list[int], start: date, end: date
) -> str:
    """Summarise `SeasonalData` for the travel months (via top attraction per district)."""
    months: set[int] = set()
    d = start
    while d <= end:
        months.add(d.month)
        d += timedelta(days=1)
    lines: list[str] = []
    month_names = SeasonalData.MONTH_NAMES
    for did in district_ids:
        top = (
            Attraction.objects.filter(district_id=did)
            .select_related("district")
            .order_by("-trend_score")
            .first()
        )
        if not top:
            continue
        rows = SeasonalData.objects.filter(
            attraction=top, month__in=sorted(months)
        ).order_by("month")
        for r in rows:
            lines.append(
                f"- {top.district.name} (sample: {top.name}) · "
                f"{month_names[r.month - 1]}: crowd={r.crowd_index:.1f}/10, "
                f"weather={r.weather_rating}/5, peak_season={r.is_peak_season}"
                + (f"; {r.visitor_note}" if r.visitor_note else "")
            )
    if not lines:
        return "No per-month seasonal rows found in DB (run `seed_seasonal_data`)."
    return "\n".join(lines)


def _distance_to_relevance(distance: float) -> float:
    """Chroma cosine distance is on [0, 2]; map to a [0, 1] relevance score."""
    try:
        d = float(distance)
    except (TypeError, ValueError):
        return 0.0
    sim = max(0.0, 1.0 - d)
    return round(min(1.0, max(0.0, sim)), 4)


def _chroma_retrieve(
    *,
    interests: list[str],
    district_ids: list[int],
    district_names: str,
    n_results: int = 8,
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    """
    Returns (audit_records, context_block, raw_rows).

    `audit_records` are safe to serialise to the API (no raw chunk text).
    """
    audit: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    context_lines: list[str] = []

    search_query = (
        f"tourist attractions {' '.join(interests)} Sri Lanka {district_names}"
    )
    try:
        embed_client = get_embedding_client()
        collection = get_collection()
        embedding = embed_client.embed(search_query, purpose="query")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Embedding / Chroma setup failed: %s", exc)
        return (
            audit,
            "(Retrieval unavailable — proceeding with database hints only.)",
            rows,
        )

    where = {"$and": [{"district_id": {"$in": district_ids}}, {"category": {"$in": interests}}]}
    result: dict[str, Any] | None = None
    try:
        result = collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Filtered Chroma query failed, retrying broadly: %s", exc)
        result = None

    ids_row = (result.get("ids") or [[]])[0] if result else []
    if not ids_row:
        try:
            result = collection.query(
                query_embeddings=[embedding], n_results=n_results
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Chroma query failed: %s", exc)
            return (
                audit,
                "(No Chroma results — proceeding with database hints only.)",
                rows,
            )

    ids = (result.get("ids") or [[]])[0]
    if not ids:
        return (
            audit,
            "(No Chroma results — proceeding with database hints only.)",
            rows,
        )
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    dists = (result.get("distances") or [[]])[0]

    slug_to_name: dict[str, str] = {}
    try:
        slugs = {
            str(m.get("slug") or "")
            for m in metas
            if m and m.get("slug")
        }
        slugs.discard("")
        if slugs:
            for a in Attraction.objects.filter(slug__in=slugs).only("slug", "name"):
                slug_to_name[a.slug] = a.name
    except Exception:  # noqa: BLE001
        pass

    for i, doc_id in enumerate(ids):
        doc = docs[i] if i < len(docs) else ""
        meta = metas[i] if i < len(metas) else {}
        meta = meta or {}
        dist = dists[i] if i < len(dists) else 1.0
        rel = _distance_to_relevance(dist)
        slug = str(meta.get("slug") or "")
        title = slug_to_name.get(slug) or slug or f"chunk-{doc_id}"
        audit.append(
            {"doc_id": str(doc_id), "attraction": title, "relevance": rel}
        )
        rows.append({"id": doc_id, "text": doc or "", "meta": meta, "relevance": rel})
        excerpt = (doc or "")[:900]
        context_lines.append(
            f"[doc_id={doc_id} slug={slug or '—'} relevance≈{rel}]\n{excerpt}"
        )

    context_block = "\n\n".join(context_lines) if context_lines else ""
    return audit, context_block, rows


# ───────────────────────── JSON + normalisation ──────────────────────
def _strip_fences(raw: str) -> str:
    return re.sub(
        r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE
    ).strip()


def _extract_retry_delay(exc: Exception) -> float | None:
    """Parse the retry delay from a Gemini 429 error message."""
    msg = str(exc)
    if "429" not in msg:
        return None
    # Match "retry in 56.81255321s" or "retry_delay { seconds: 57 }"
    m = re.search(r"retry in ([\d.]+)s", msg, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"seconds:\s*(\d+)", msg)
    if m:
        return float(m.group(1))
    return 5.0  # conservative default for 429s to prevent 60s frontend timeout


def _parse_json_with_retry(
    *, model_primary: Any, model_fallback: Any | None, prompt: str
) -> dict | None:
    models = [model_primary] + ([model_fallback] if model_fallback else [])
    follow = (
        "\n\nYour previous response was not valid JSON. "
        "Reply again with ONLY a single JSON object matching the schema. "
        "No markdown fences, no commentary."
    )

    # Two rounds: the first sends the plain prompt, the second re-asks with an
    # explicit "valid JSON only" nudge. One try per round keeps the call count
    # low — the sequential-day generator is the real safety net above this.
    for round_i in range(2):
        active_prompt = prompt if round_i == 0 else prompt + follow
        attempt = 0
        delay = 2.0
        while attempt < 1:
            for model in models:
                try:
                    response = model.generate_content(
                        active_prompt,
                        generation_config={
                            "max_output_tokens": MAX_OUTPUT_TOKENS,
                            "temperature": 0.45,
                            "top_p": 0.95,
                            "response_mime_type": "application/json",
                        },
                    )
                    text = (getattr(response, "text", "") or "").strip()
                    if not text:
                        text = _extract_text_from_response(response).strip()
                    if not text:
                        continue
                    cleaned = _strip_fences(text)
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    logger.warning("Itinerary JSON parse failed (round %s)", round_i)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Gemini itinerary call failed (attempt %s): %s",
                        attempt + 1,
                        exc,
                    )
                    # On rate-limit errors, wait the suggested delay and
                    # skip the fallback model (it shares the same quota).
                    retry_wait = _extract_retry_delay(exc)
                    if retry_wait is not None:
                        logger.info(
                            "Rate-limited — waiting %.0fs before retry", retry_wait
                        )
                        time.sleep(min(retry_wait + 1, 30))
                        break  # skip remaining models, go to next attempt
            else:
                # Only sleep the normal backoff if we weren't rate-limited
                time.sleep(delay)
            delay = min(delay * 2, 8)
            attempt += 1
    return None


def _extract_text_from_response(response: Any) -> str:
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


def _district_map(district_ids: list[int]) -> dict[str, int]:
    return {
        d.name.lower(): d.id
        for d in District.objects.filter(id__in=district_ids)
    }


def _day_stop_fingerprint(stops: list[dict]) -> tuple[int, ...]:
    ids: list[int] = []
    for stop in stops:
        aid = stop.get("attraction_id")
        if isinstance(aid, int):
            ids.append(aid)
    return tuple(sorted(ids))


def _llm_plan_has_duplicate_days(days: list[dict]) -> bool:
    seen: set[tuple[str, ...]] = set()
    for day in days:
        names = tuple(
            sorted(
                (s.get("name") or "").strip().lower()
                for s in (day.get("stops") or [])
                if (s.get("name") or "").strip()
            )
        )
        if not names:
            continue
        if names in seen:
            return True
        seen.add(names)
    return False


def _internal_plan_needs_sequential_fallback(
    *, internal: dict, num_days: int
) -> bool:
    days = internal.get("days") or []
    if len(days) < num_days:
        return True
    fingerprints = [_day_stop_fingerprint(d.get("stops") or []) for d in days]
    non_empty = [fp for fp in fingerprints if fp]
    if len(non_empty) < num_days:
        return True
    if len(set(non_empty)) < len(non_empty):
        return True
    return False


def _convert_llm_plan(
    data: dict,
    pool: list[AttractionContext],
    district_ids: list[int],
) -> dict:
    """Map LLM JSON (names) → internal structure with `district_id` + `attraction_id`."""
    dmap = _district_map(district_ids)
    by_id = {a.id: a for a in pool}
    by_name: dict[str, AttractionContext] = {}
    for a in pool:
        by_name[a.name.lower()] = a

    def resolve_attraction(name: str) -> int | None:
        key = name.strip().lower()
        if key in by_name:
            return by_name[key].id
        for a in pool:
            if key in a.name.lower() or a.name.lower() in key:
                return a.id
        return None

    out_days: list[dict] = []
    for idx, day in enumerate(data.get("days") or []):
        dname = (day.get("district") or "").strip()
        did = dmap.get(dname.lower())
        if not did and district_ids:
            did = district_ids[idx % len(district_ids)]
        theme = day.get("theme") or ""
        accom = day.get("accommodation_note") or ""
        notes_parts = [theme, accom, day.get("notes")]
        notes = " — ".join(p for p in notes_parts if p) or "Planned day"

        stops_out: list[dict] = []
        for s in day.get("stops") or []:
            name = (s.get("name") or "").strip()
            if not name:
                continue
            aid = resolve_attraction(name)
            if aid is None or aid not in by_id:
                continue
            desc = (s.get("description") or "").strip()
            tip = (s.get("tip") or "").strip()
            tip_merged = " ".join(p for p in [desc, tip] if p)
            stops_out.append(
                {
                    "attraction_id": aid,
                    "name": by_id[aid].name,
                    "arrival_time": s.get("arrival_time"),
                    "duration_mins": s.get("duration_mins"),
                    "tip": tip_merged or "Confirm opening hours before visiting.",
                }
            )
        if did and stops_out:
            out_days.append(
                {
                    "day": day.get("day"),
                    "district_id": did,
                    "notes": notes,
                    "stops": stops_out,
                }
            )

    footers: list[str] = []
    if data.get("budget_note"):
        footers.append(str(data["budget_note"]))
    if data.get("best_transport"):
        footers.append("Transport: " + str(data["best_transport"]))
    return {
        "title": data.get("title"),
        "days": out_days,
        "_footer": " | ".join(footers),
    }


def _normalize_plan(
    *, plan: dict, pool: list[AttractionContext], preferences: dict
) -> dict:
    """Ensure exactly `num_days`, de-duplicate stops, pad from the relational pool."""
    num_days = int(preferences["num_days"])
    district_ids = list(preferences["district_ids"])
    by_id = {a.id: a for a in pool}
    by_district: dict[int, list[int]] = {}
    for a in pool:
        by_district.setdefault(a.district_id, []).append(a.id)

    footer = plan.get("_footer") or ""
    input_days = plan.get("days") or []
    normalized_days: list[dict] = []
    used_global: set[int] = set()
    seen_fingerprints: set[tuple[int, ...]] = set()

    for i in range(num_days):
        src = input_days[i] if i < len(input_days) else {}
        day_number = i + 1
        district_id = district_ids[i % len(district_ids)] if district_ids else None
        src_district = src.get("district_id")
        if src_district and len(district_ids) <= 1:
            district_id = src_district

        src_stops = list(src.get("stops") or [])
        src_fp = _day_stop_fingerprint(src_stops)
        if src_fp and src_fp in seen_fingerprints:
            src_stops = []

        candidate_pool = by_district.get(district_id) or list(by_id.keys())
        day_stops: list[dict] = []
        day_seen: set[int] = set()

        for stop in src_stops:
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

        if len(day_stops) < 3:
            fill_order = candidate_pool + [
                aid for aid in by_id if aid not in candidate_pool
            ]
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

        if len(day_stops) < 1 and candidate_pool:
            attraction_id = next(
                (aid for aid in candidate_pool if aid not in used_global),
                candidate_pool[i % len(candidate_pool)],
            )
            att = by_id[attraction_id]
            day_stops.append(
                {
                    "attraction_id": attraction_id,
                    "name": att.name,
                    "duration_mins": 120,
                    "tip": "Limited dataset; core suggestion.",
                }
            )

        cleaned_stops: list[dict] = []
        for order, stop in enumerate(day_stops, start=1):
            attraction_id = stop["attraction_id"]
            cleaned_stops.append(
                {
                    "attraction_id": attraction_id,
                    "name": stop.get("name") or by_id[attraction_id].name,
                    "stop_order": order,
                    "arrival_time": stop.get("arrival_time")
                    or _suggested_time(order - 1),
                    "duration_mins": int(stop.get("duration_mins") or 120),
                    "tip": stop.get("tip") or "Best visited during daylight hours.",
                }
            )

        notes = src.get("notes") or f"Day {day_number} — explore a fresh set of highlights."
        if footer and i == 0:
            notes = f"{notes}\n\n{footer}".strip()

        day_fp = _day_stop_fingerprint(cleaned_stops)
        if day_fp:
            seen_fingerprints.add(day_fp)

        normalized_days.append(
            {
                "day": day_number,
                "district_id": district_id,
                "notes": notes,
                "stops": cleaned_stops,
            }
        )

    plan["days"] = normalized_days
    plan["title"] = plan.get("title") or f"{num_days}-Day Sri Lanka Trip"
    return plan


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


# ───────────────────────── Service ───────────────────────────────────
class ItineraryService:
    def __init__(self, gemini_client: Any | None = None):
        if gemini_client is not None:
            self._gemini = gemini_client
            self._gemini_fallback = None
        else:
            from lankaguide.services.llm_client import get_llm

            try:
                self._gemini = get_llm("itinerary")
                self._gemini_fallback = None
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(
                    f"Failed to initialise Groq for itinerary: {exc}"
                ) from exc

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
        district_names = _district_name_list(preferences["district_ids"])
        seasons = _district_season_context(preferences["district_ids"])
        seasonal_notes = _seasonal_window_notes(
            preferences["district_ids"],
            preferences["start_date"],
            preferences["end_date"],
        )
        top_hints = _top_attractions_hints(preferences["district_ids"], n=3)

        duration_days = int(preferences["num_days"])
        n_results = min(24, 8 + duration_days * 2)

        audit, rag_context_block, _rows = _chroma_retrieve(
            interests=preferences["interests"],
            district_ids=preferences["district_ids"],
            district_names=district_names,
            n_results=n_results,
        )
        rag_used = bool(audit)

        CONTEXT = f"""
=== RETRIEVED KNOWLEDGE ===
{rag_context_block or "(no vector hits — use DATABASE HINTS and stay within Sri Lanka tourism facts you know to be widely accepted)."}
=== END RETRIEVED KNOWLEDGE ===
""".strip()

        climate_block = "\n".join(s.as_prompt_line() for s in seasons)

        SEASONAL = f"""
=== SEASONAL NOTES ===
Travel period: {preferences['start_date']} to {preferences['end_date']}
Districts selected: {district_names}
Climate / peak snapshot:
{climate_block}

Monthly crowd & weather during trip months (representative top attraction / district):
{seasonal_notes}

=== DATABASE HINTS (top attractions by district — verified rows) ===
{top_hints}
=== END DATABASE HINTS ===
=== END SEASONAL NOTES ===
""".strip()

        user_req = f"""
User request:
- Duration: {duration_days} days ({preferences['start_date']} to {preferences['end_date']})
- Budget: LKR {preferences['budget_lkr']} total
- Interests: {", ".join(preferences["interests"])}
- Group: {preferences['group_size']} {preferences['group_type']}
- Districts of interest: {district_names}
Generate a complete {duration_days}-day itinerary with exactly {duration_days} unique
days in the "days" array. Each day must list different attractions — never repeat
the same stops on multiple days.
""".strip()

        final_prompt = "\n\n".join(
            [
                ITINERARY_SYSTEM,
                CONTEXT,
                SEASONAL,
                OUTPUT_SCHEMA_BLOCK,
                user_req,
            ]
        )

        plan_raw = _parse_json_with_retry(
            model_primary=self._gemini,
            model_fallback=self._gemini_fallback,
            prompt=final_prompt,
        )
        bulk_days = (plan_raw or {}).get("days") or []
        needs_sequential = duration_days > 1 and (
            plan_raw is None
            or len(bulk_days) < duration_days
            or _llm_plan_has_duplicate_days(bulk_days)
        )
        if needs_sequential:
            logger.info(
                "Bulk itinerary incomplete or duplicated (%s days returned); "
                "using sequential day generation.",
                len(bulk_days),
            )
            plan_raw = self._generate_sequential_days(
                preferences=preferences,
                context_block=CONTEXT,
                seasonal_block=SEASONAL,
                district_names=district_names,
            )

        if plan_raw is None:
            raise RuntimeError(
                "AI planner could not return valid JSON after retries. Please try again."
            )

        internal = _convert_llm_plan(
            plan_raw,
            pool=pool,
            district_ids=preferences["district_ids"],
        )
        if _internal_plan_needs_sequential_fallback(
            internal=internal, num_days=duration_days
        ) and duration_days > 1:
            logger.info(
                "Converted itinerary still lacks unique days; retrying sequentially."
            )
            plan_raw = self._generate_sequential_days(
                preferences=preferences,
                context_block=CONTEXT,
                seasonal_block=SEASONAL,
                district_names=district_names,
            )
            if plan_raw is not None:
                internal = _convert_llm_plan(
                    plan_raw,
                    pool=pool,
                    district_ids=preferences["district_ids"],
                )
        if not internal.get("days"):
            raise RuntimeError(
                "The model produced no usable days matching your districts."
            )
        plan = _normalize_plan(plan=internal, pool=pool, preferences=preferences)

        return self._persist(
            user=user,
            preferences=preferences,
            plan=plan,
            rag_used=rag_used,
            retrieval_audit=audit,
        )

    def _generate_sequential_days(
        self,
        *,
        preferences: dict,
        context_block: str,
        seasonal_block: str,
        district_names: str,
    ) -> dict | None:
        """Generate one day at a time so later days cannot copy earlier ones."""
        num_days = int(preferences["num_days"])
        district_ids = list(preferences["district_ids"])
        id_to_name = {
            d.id: d.name
            for d in District.objects.filter(id__in=district_ids).only("id", "name")
        }
        merged: dict[str, Any] = {"days": []}
        used_names: list[str] = []

        for day_num in range(1, num_days + 1):
            focus_id = district_ids[(day_num - 1) % len(district_ids)]
            focus_name = id_to_name.get(focus_id, district_names)
            avoid = ", ".join(used_names) or "none yet"
            day_req = f"""
Generate ONLY Day {day_num} of {num_days} for this Sri Lanka trip.
Focus district for today: {focus_name}
Do NOT include these attractions already used on earlier days: {avoid}
Each stop must be a different attraction from all previous days.
Output JSON with a "days" array containing exactly one day object with "day": {day_num}.
""".strip()
            schema = SINGLE_DAY_SCHEMA_BLOCK.format(day_number=day_num)
            prompt = "\n\n".join(
                [
                    ITINERARY_SYSTEM,
                    context_block,
                    seasonal_block,
                    schema,
                    day_req,
                ]
            )
            day_raw = _parse_json_with_retry(
                model_primary=self._gemini,
                model_fallback=self._gemini_fallback,
                prompt=prompt,
            )
            if not day_raw or not day_raw.get("days"):
                continue
            day_obj = day_raw["days"][0]
            day_obj["day"] = day_num
            merged["days"].append(day_obj)
            if day_raw.get("title") and not merged.get("title"):
                merged["title"] = day_raw["title"]
            for stop in day_obj.get("stops") or []:
                name = (stop.get("name") or "").strip()
                if name:
                    used_names.append(name)

        if not merged["days"]:
            return None
        merged.setdefault("title", f"{num_days}-Day Sri Lanka Trip")
        return merged

    @transaction.atomic
    def regenerate_day(self, *, itinerary: Itinerary, day_number: int) -> ItineraryDay:
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
            interests=[s.attraction.category for s in day.stops.all()]
            or ["cultural"],
            district_ids=all_districts,
        )
        if not pool:
            return day

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

    @staticmethod
    def _persist(
        *,
        user,
        preferences: dict,
        plan: dict,
        rag_used: bool,
        retrieval_audit: list[dict[str, Any]],
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
            rag_used=rag_used,
            retrieved_doc_ids=retrieval_audit,
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
