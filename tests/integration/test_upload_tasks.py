from __future__ import annotations

from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.common.exceptions import PDFProcessingError
from apps.courses.factories import CourseFactory
from apps.uploads.models import UserMaterial
from apps.uploads.tasks import process_pdf_task


def _material() -> UserMaterial:
    course = CourseFactory()
    material = UserMaterial(course=course, filename="lecture.pdf")
    material.filepath.save("lecture.pdf", SimpleUploadedFile("lecture.pdf", b"%PDF-1.4"))
    material.save()
    return material


@pytest.mark.django_db
def test_page_limit_error_is_recorded_and_not_retried():
    """Regression test: PDFProcessingError (e.g. the 100-page limit) used to
    be swallowed by a blanket `except Exception: retry`, silently retrying a
    file that will always fail the same way, with no visible reason anywhere
    on the UserMaterial record."""
    material = _material()

    with patch(
        "apps.uploads.tasks.process_pdf_file",
        side_effect=PDFProcessingError("PDF has 150 pages; limit is 100"),
    ):
        with pytest.raises(PDFProcessingError):
            process_pdf_task(str(material.id))

    material.refresh_from_db()
    assert material.embedding_status is False
    assert "150" in material.processing_error


@pytest.mark.django_db
def test_transient_error_is_retried_and_recorded():
    material = _material()

    with patch("apps.uploads.tasks.process_pdf_file", side_effect=ConnectionError("boom")):
        with pytest.raises(Exception):  # Celery raises a Retry in eager mode
            process_pdf_task(str(material.id))

    material.refresh_from_db()
    assert "Временная ошибка" in material.processing_error


@pytest.mark.django_db
def test_successful_processing_clears_previous_error():
    material = _material()
    material.processing_error = "предыдущая ошибка"
    material.save(update_fields=["processing_error"])

    with patch("apps.uploads.tasks.process_pdf_file", return_value=3):
        process_pdf_task(str(material.id))

    material.refresh_from_db()
    assert material.processing_error == ""
