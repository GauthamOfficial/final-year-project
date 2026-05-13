"""Helpers for seasonal demand / crowd curves (Gap 8)."""

from __future__ import annotations

MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def best_month_indices(monthly_rows: list) -> list[int]:
    """Months where weather_rating >= 4 and crowd_index < 8."""
    out = []
    for row in monthly_rows:
        if isinstance(row, dict):
            w = row.get("weather_rating")
            c = row.get("crowd_index")
            m = row.get("month")
        else:
            w = getattr(row, "weather_rating", None)
            c = getattr(row, "crowd_index", None)
            m = getattr(row, "month", None)
        if w is not None and c is not None and m is not None:
            if int(w) >= 4 and float(c) < 8.0:
                out.append(int(m))
    return sorted(out)


def best_month_names(monthly_rows: list) -> list[str]:
    return [MONTH_NAMES[i - 1] for i in best_month_indices(monthly_rows)]


def peak_month_indices(monthly_rows: list) -> list[int]:
    out = []
    for row in monthly_rows:
        if isinstance(row, dict):
            peak = row.get("is_peak_season")
            m = row.get("month")
        else:
            peak = getattr(row, "is_peak_season", None)
            m = getattr(row, "month", None)
        if m is not None and peak:
            out.append(int(m))
    return sorted(out)
