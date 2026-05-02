"""
`python manage.py fetch_wikimedia_images`

Pulls real photography from Wikimedia Commons for every Attraction in the
database. For each attraction:

  1. Resolve the Wikipedia page using `wikipedia_title` (or falls back to
     the attraction name).
  2. Fetch the page's `pageimage` (the lead image) plus up to 5 additional
     gallery images via the MediaWiki API.
  3. Download each image into `MEDIA_ROOT/attractions/<slug>/<idx>.<ext>`.
  4. Create a `MediaAsset` row with attribution, license and the
     Wikipedia source URL.

Idempotent: re-running skips attractions that already have media unless
`--force` is supplied.

Optional:
  --district DISTRICT   only refresh attractions inside a given district
  --slug SLUG           only refresh a specific attraction
  --limit N             cap the number of attractions processed
  --force               re-download even if media already exists
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Iterable

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.attractions.models import Attraction, MediaAsset, MediaType

logger = logging.getLogger("lankaguide.media.wikimedia")

WIKI_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "LankaGuide/1.0 (https://lankaguide.lk; ops@lankaguide.lk)"

ALLOWED_EXTS = (".jpg", ".jpeg", ".png", ".webp")
SKIP_KEYWORDS = (
    "logo", "icon", "flag", "coat_of_arms", "map_of", "locator",
    "wiki", "stub", "commons-logo", "question_book",
)
MAX_GALLERY = 5
TIMEOUT = 20


class Command(BaseCommand):
    help = "Fetch Wikimedia Commons images for every attraction."

    def add_arguments(self, parser):
        parser.add_argument("--district", type=str, default=None)
        parser.add_argument("--slug", type=str, default=None)
        parser.add_argument("--limit", type=int, default=None)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **opts):
        qs = Attraction.objects.select_related("district").order_by("id")
        if opts.get("district"):
            qs = qs.filter(district__name__iexact=opts["district"])
        if opts.get("slug"):
            qs = qs.filter(slug=opts["slug"])
        if opts.get("limit"):
            qs = qs[: opts["limit"]]

        force = bool(opts.get("force"))
        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)

        downloaded = 0
        skipped = 0
        for attraction in qs:
            existing = attraction.media.filter(type=MediaType.IMAGE).count()
            if existing and not force:
                skipped += 1
                continue

            title = attraction.wikipedia_title or attraction.name
            self.stdout.write(
                f">> {attraction.name} (page='{title}', district={attraction.district.name})"
            )
            images = self._resolve_images(title)
            if not images:
                self.stdout.write(
                    self.style.WARNING(f"   no images returned for '{title}'")
                )
                continue

            if force:
                # Wipe local files referenced by old MediaAsset rows.
                for old in attraction.media.filter(type=MediaType.IMAGE):
                    try:
                        path = media_root / old.s3_key.replace("media/", "")
                        if path.exists():
                            path.unlink()
                    except Exception:
                        pass
                attraction.media.filter(type=MediaType.IMAGE).delete()

            target_dir = media_root / "attractions" / attraction.slug
            target_dir.mkdir(parents=True, exist_ok=True)

            for idx, img in enumerate(images[: MAX_GALLERY + 1]):
                ext = self._ext(img["url"])
                if ext.lower() not in ALLOWED_EXTS:
                    continue
                filename = f"{idx}{ext}"
                dest = target_dir / filename
                if not dest.exists() or force:
                    if not self._download(img["url"], dest):
                        continue
                rel = f"attractions/{attraction.slug}/{filename}"
                MediaAsset.objects.create(
                    attraction=attraction,
                    type=MediaType.IMAGE,
                    s3_key=f"media/{rel}",
                    cdn_url=f"{settings.MEDIA_URL}{rel}",
                    is_featured=(idx == 0),
                    caption=img.get("caption", "") or attraction.name,
                    attribution=img.get("attribution", "Wikimedia Commons"),
                    license=img.get("license", ""),
                    source_url=img.get("source_url", ""),
                )
                downloaded += 1

            time.sleep(0.5)  # be a polite Wikimedia citizen

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Downloaded {downloaded} images. Skipped {skipped} "
                f"attractions that already had media."
            )
        )

    # ─────────────────── Wikimedia API ─────────────────────────────────
    def _resolve_images(self, title: str) -> list[dict[str, str]]:
        """Returns [{"url", "caption", "attribution", "license", "source_url"}, ...]."""
        page = self._wiki_page(title)
        if not page:
            return []
        out: list[dict[str, str]] = []

        # Lead image (pageimage)
        original = page.get("original", {}) or {}
        if original.get("source"):
            url = original["source"]
            meta = self._image_meta(url)
            out.append(
                {
                    "url": url,
                    "caption": page.get("title", title),
                    "attribution": meta.get("artist", "Wikimedia Commons"),
                    "license": meta.get("license", ""),
                    "source_url": page.get(
                        "fullurl", f"https://en.wikipedia.org/wiki/{title}"
                    ),
                }
            )

        # Gallery images
        for fname in self._page_images(page.get("title", title)):
            if any(k in fname.lower() for k in SKIP_KEYWORDS):
                continue
            commons_url = self._commons_image_url(fname)
            if not commons_url:
                continue
            meta = self._image_meta(commons_url)
            out.append(
                {
                    "url": commons_url,
                    "caption": fname.replace("File:", ""),
                    "attribution": meta.get("artist", "Wikimedia Commons"),
                    "license": meta.get("license", ""),
                    "source_url": (
                        f"https://commons.wikimedia.org/wiki/"
                        f"{fname.replace(' ', '_')}"
                    ),
                }
            )
            if len(out) > MAX_GALLERY:
                break

        # De-dupe by url, preserve order
        seen: set[str] = set()
        unique: list[dict[str, str]] = []
        for it in out:
            if it["url"] in seen:
                continue
            seen.add(it["url"])
            unique.append(it)
        return unique

    def _wiki_page(self, title: str) -> dict[str, Any] | None:
        params = {
            "action": "query",
            "format": "json",
            "prop": "pageimages|info",
            "piprop": "original|name",
            "inprop": "url",
            "redirects": "1",
            "titles": title,
        }
        try:
            r = requests.get(
                WIKI_API,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.debug("wiki query failed for %s: %s", title, exc)
            return None
        pages = (r.json().get("query", {}) or {}).get("pages", {}) or {}
        for _, page in pages.items():
            if page.get("missing"):
                return None
            return page
        return None

    def _page_images(self, title: str) -> list[str]:
        params = {
            "action": "query",
            "format": "json",
            "prop": "images",
            "imlimit": "20",
            "redirects": "1",
            "titles": title,
        }
        try:
            r = requests.get(
                WIKI_API,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
        except Exception:  # noqa: BLE001
            return []
        pages = (r.json().get("query", {}) or {}).get("pages", {}) or {}
        for _, page in pages.items():
            return [img["title"] for img in page.get("images", []) if img.get("title")]
        return []

    def _commons_image_url(self, fname: str) -> str | None:
        params = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url",
            "titles": fname,
        }
        try:
            r = requests.get(
                COMMONS_API,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
        except Exception:  # noqa: BLE001
            return None
        pages = (r.json().get("query", {}) or {}).get("pages", {}) or {}
        for _, page in pages.items():
            ii = page.get("imageinfo", []) or []
            if ii:
                return ii[0].get("url")
        return None

    def _image_meta(self, url: str) -> dict[str, str]:
        # Best-effort attribution fetch from Commons
        try:
            fname = "File:" + url.rsplit("/", 1)[-1]
            params = {
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "iiprop": "extmetadata",
                "titles": fname,
            }
            r = requests.get(
                COMMONS_API,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            pages = (r.json().get("query", {}) or {}).get("pages", {}) or {}
            for _, page in pages.items():
                meta = (page.get("imageinfo") or [{}])[0].get("extmetadata", {}) or {}
                return {
                    "artist": _strip_html((meta.get("Artist") or {}).get("value", ""))
                    or "Wikimedia Commons",
                    "license": (meta.get("LicenseShortName") or {}).get("value", "")
                    or (meta.get("License") or {}).get("value", ""),
                }
        except Exception:  # noqa: BLE001
            pass
        return {"artist": "Wikimedia Commons", "license": ""}

    # ─────────────────── Download ─────────────────────────────────────
    def _download(self, url: str, dest: Path) -> bool:
        try:
            r = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
                stream=True,
            )
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.debug("download failed (%s): %s", url, exc)
            try:
                if dest.exists():
                    dest.unlink()
            except Exception:
                pass
            return False

    @staticmethod
    def _ext(url: str) -> str:
        path = url.split("?")[0].split("#")[0]
        _, ext = os.path.splitext(path)
        return ext or ".jpg"


def _strip_html(s: str) -> str:
    import re

    s = re.sub(r"<[^>]+>", "", s or "")
    return s.strip()
