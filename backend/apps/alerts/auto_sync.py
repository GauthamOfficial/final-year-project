"""
On-demand auto-refresh for weather safety alerts.

The `/api/v1/alerts/` endpoints call :func:`ensure_alerts_fresh`, which kicks
off a background `sync_weather_alerts` run at most once per
``ALERTS_AUTO_SYNC_SECONDS`` (default 3h). This keeps the alerts page showing
live Open-Meteo data without anyone running a management command — while never
blocking the HTTP request that triggered it.

Why an in-process guard (not the Django cache)?
  - The cache is Redis with ``IGNORE_EXCEPTIONS=True``; if Redis is down a
    cache-based lock silently misbehaves and could trigger a sync per request.
  - A module-level timestamp + lock is Redis-independent. With multiple
    gunicorn workers each may sync once per interval, but
    ``WeatherAlertService.sync_weather_alerts`` de-duplicates rows (same
    title/district within 6h), so no duplicates are created.
"""

from __future__ import annotations

import logging
import threading
import time

from django.conf import settings

logger = logging.getLogger("lankaguide.alerts.auto_sync")

# Refresh at most this often (seconds). Overridable via settings.
AUTO_SYNC_INTERVAL = int(getattr(settings, "ALERTS_AUTO_SYNC_SECONDS", 3 * 3600))

_state_lock = threading.Lock()
_state = {"last": 0.0, "running": False}


def _background_sync() -> None:
    from django.db import connection

    from lankaguide.services.weather_service import WeatherAlertService

    try:
        created, deactivated = WeatherAlertService().sync_weather_alerts()
        logger.info(
            "auto alert sync: +%s created, %s deactivated", created, deactivated
        )
    except Exception:  # noqa: BLE001
        logger.exception("auto weather-alert sync failed")
    finally:
        # Don't leak this thread's DB connection.
        connection.close()
        with _state_lock:
            _state["running"] = False
            # Stamp regardless of success so a persistent upstream outage
            # can't make us re-sync on every page load; it retries next interval.
            _state["last"] = time.monotonic()


def ensure_alerts_fresh(*, force: bool = False) -> bool:
    """
    Trigger a background weather-alert sync if the data is stale.

    Returns True if a sync was started by this call, False otherwise.
    Never blocks: the sync runs in a daemon thread.
    """
    now = time.monotonic()
    with _state_lock:
        if _state["running"]:
            return False
        if not force and (now - _state["last"]) < AUTO_SYNC_INTERVAL:
            return False
        _state["running"] = True

    threading.Thread(
        target=_background_sync, name="alert-auto-sync", daemon=True
    ).start()
    return True
