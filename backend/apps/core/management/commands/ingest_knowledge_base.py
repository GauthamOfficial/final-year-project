"""
`python manage.py ingest_knowledge_base` — Prompt 3A.

Walks `data/knowledge/` (configurable via --path), extracts text from
`.txt` and `.pdf` files, chunks each document into 512-token segments with
64-token overlap, embeds each chunk via Gemini (with offline fallback),
and upserts into the `sri_lanka_tourism` ChromaDB collection.

Filename metadata convention (parsed by `_metadata_from_path`):

    <district_id>__<attraction_id>__<category>__<slug>.txt
    e.g. 5__123__cultural__sigiriya-rock-fortress.txt

Anything missing in the filename is left as `None` so `where=` filters in
PRD §9.2 still work.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.services.chunking import batched, chunk_text
from apps.core.services.embeddings import get_embedding_client
from apps.core.services.vectorstore import get_collection

logger = logging.getLogger("lankaguide.core.ingest")

DEFAULT_KNOWLEDGE_DIR = Path(settings.BASE_DIR) / "data" / "knowledge"


class Command(BaseCommand):
    help = "Embed local knowledge documents into ChromaDB (PRD §9.1)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default=str(DEFAULT_KNOWLEDGE_DIR),
            help="Directory containing .txt / .pdf source files.",
        )
        parser.add_argument(
            "--collection",
            default=settings.CHROMA_COLLECTION,
            help="Target ChromaDB collection name.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=16,
            help="Embedding batch size (smaller = more API calls but lower memory).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Drop and recreate the collection before ingesting.",
        )

    # ─────────────────── File loaders ──────────────────────────────────
    @staticmethod
    def _read_txt(path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def _read_pdf(path: Path) -> str:
        try:
            import pdfplumber
        except ImportError as exc:  # pragma: no cover
            raise CommandError(
                "pdfplumber is not installed. Run `pip install pdfplumber` to ingest PDFs."
            ) from exc
        text = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text.append(page_text)
        return "\n\n".join(text)

    @classmethod
    def _read_file(cls, path: Path) -> str:
        if path.suffix.lower() == ".txt":
            return cls._read_txt(path)
        if path.suffix.lower() == ".pdf":
            return cls._read_pdf(path)
        raise CommandError(f"Unsupported file type: {path.suffix}")

    # ─────────────────── Filename → metadata ───────────────────────────
    @staticmethod
    def _metadata_from_path(path: Path) -> dict:
        stem = path.stem
        parts = stem.split("__")
        meta: dict = {
            "source_filename": path.name,
            "source_type": path.suffix.lstrip(".").lower(),
        }

        def _maybe_int(value: str) -> int | None:
            try:
                return int(value)
            except ValueError:
                return None

        if len(parts) >= 1:
            district = _maybe_int(parts[0])
            if district is not None:
                meta["district_id"] = district
        if len(parts) >= 2:
            attraction = _maybe_int(parts[1])
            if attraction is not None:
                meta["attraction_id"] = attraction
        if len(parts) >= 3:
            meta["category"] = parts[2]
        if len(parts) >= 4:
            meta["slug"] = parts[3]
        meta.setdefault("language", "en")
        return meta

    # ─────────────────── Main flow ─────────────────────────────────────
    def handle(self, *args, **opts):
        knowledge_dir = Path(opts["path"]).expanduser().resolve()
        if not knowledge_dir.exists():
            knowledge_dir.mkdir(parents=True, exist_ok=True)
            self.stdout.write(
                self.style.WARNING(
                    f"Created empty knowledge dir at {knowledge_dir}. "
                    "Drop .txt/.pdf files there and re-run."
                )
            )
            return

        files = sorted(
            [p for p in knowledge_dir.rglob("*") if p.suffix.lower() in {".txt", ".pdf"}]
        )
        if not files:
            self.stdout.write(
                self.style.WARNING(f"No .txt or .pdf files found under {knowledge_dir}.")
            )
            return

        embed_client = get_embedding_client()
        self.stdout.write(f"Embedding backend: {embed_client.name}")

        collection = get_collection(opts["collection"])
        if opts["reset"]:
            from apps.core.services.vectorstore import get_chroma_client

            client = get_chroma_client()
            client.delete_collection(opts["collection"])
            collection = get_collection(opts["collection"])
            self.stdout.write(self.style.WARNING(f"Reset collection '{opts['collection']}'."))

        total_chunks = 0
        for path in files:
            meta = self._metadata_from_path(path)
            self.stdout.write(f"  - {path.name} -> {meta}")
            text = self._read_file(path)
            chunks = chunk_text(text)
            if not chunks:
                self.stdout.write(self.style.NOTICE("    (empty / unreadable)"))
                continue

            for batch in batched(enumerate(chunks), opts["batch_size"]):
                ids: list[str] = []
                docs: list[str] = []
                metas: list[dict] = []
                for chunk_index, chunk in batch:
                    file_hash = hashlib.sha1(path.read_bytes()).hexdigest()[:12]
                    chunk_id = f"{path.stem}::c{chunk_index:03d}::{file_hash}"
                    ids.append(chunk_id)
                    docs.append(chunk.text)
                    metas.append(
                        {
                            **meta,
                            "chunk_index": chunk_index,
                            "token_estimate": chunk.token_estimate,
                        }
                    )
                embeddings = embed_client.embed_batch(docs)
                collection.upsert(
                    ids=ids,
                    documents=docs,
                    metadatas=metas,
                    embeddings=embeddings,
                )
                total_chunks += len(ids)

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingested {total_chunks} chunks from {len(files)} files into "
                f"'{opts['collection']}' at {settings.CHROMA_PERSIST_DIR}."
            )
        )
