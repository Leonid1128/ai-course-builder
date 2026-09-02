from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from apps.ai_agents.adapters.django_vector_store import cosine_similarity, lexical_score
from apps.common.exceptions import PDFProcessingError
from apps.uploads.services.pdf_processor import extract_pdf_text, split_text


def test_split_text_respects_overlap() -> None:
    chunks = split_text("abcdefghij", chunk_size=4, overlap=1)
    assert chunks[0] == "abcd"
    assert chunks[1].startswith("d")


def test_cosine_similarity_identical() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)


def test_lexical_score() -> None:
    assert lexical_score("граф дерево", "граф и дерево в дискретке") > 0.5


def test_pdf_page_limit() -> None:
    reader = MagicMock()
    reader.pages = [MagicMock() for _ in range(101)]
    with patch("apps.uploads.services.pdf_processor.PdfReader", return_value=reader):
        with pytest.raises(PDFProcessingError, match="101"):
            extract_pdf_text("dummy.pdf", max_pages=100)
