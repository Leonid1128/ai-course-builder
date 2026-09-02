from __future__ import annotations

import logging

from django.conf import settings
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from apps.common.exceptions import PDFProcessingError
from apps.common.interfaces import EmbeddingClientProtocol
from apps.uploads.models import MaterialEmbedding, UserMaterial

logger = logging.getLogger(__name__)


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    overlap = max(0, min(overlap, chunk_size - 1))
    chunks: list[str] = []
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(start + chunk_size, length)
        chunks.append(cleaned[start:end])
        if end == length:
            break
        start = end - overlap
    return chunks


def extract_pdf_text(path: str, max_pages: int) -> tuple[str, int]:
    try:
        reader = PdfReader(path)
    except (PdfReadError, OSError) as exc:
        raise PDFProcessingError(f"Cannot read PDF: {exc}") from exc

    page_count = len(reader.pages)
    if page_count > max_pages:
        raise PDFProcessingError(
            f"PDF has {page_count} pages; limit is {max_pages} (TZ §3)"
        )

    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages), page_count


def process_pdf_file(
    material: UserMaterial,
    *,
    embedding_client: EmbeddingClientProtocol | None = None,
    max_pages: int | None = None,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> int:
    max_pages = max_pages if max_pages is not None else settings.MAX_PDF_PAGES
    chunk_size = chunk_size if chunk_size is not None else settings.PDF_CHUNK_SIZE
    overlap = overlap if overlap is not None else settings.PDF_CHUNK_OVERLAP

    text, page_count = extract_pdf_text(material.filepath.path, max_pages)
    chunks = split_text(text, chunk_size, overlap)
    vectors: list[list[float]] = []
    if embedding_client is not None and chunks:
        try:
            vectors = embedding_client.embed(chunks)
        except Exception:
            logger.exception("Embedding failed for material %s; storing text-only chunks", material.id)
            vectors = []

    material.chunks.all().delete() # type: ignore[attr-defined]
    for index, chunk in enumerate(chunks):
        vector = vectors[index] if index < len(vectors) else []
        MaterialEmbedding.objects.create(
            material=material,
            chunk_text=chunk,
            embedding_vector=vector,
            chunk_metadata={"source": material.filename, "index": index, "pages": page_count},
        )

    material.page_count = page_count
    material.embedding_status = True
    material.save(update_fields=["page_count", "embedding_status"])
    return len(chunks)
