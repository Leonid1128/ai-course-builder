from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings

from apps.ai_agents.adapters.embeddings import build_embedding_client
from apps.common.exceptions import PDFProcessingError
from apps.uploads.models import UserMaterial
from apps.uploads.services.pdf_processor import process_pdf_file

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_pdf_task(self, material_id: str) -> dict[str, int]:
    material = UserMaterial.objects.get(id=material_id)
    try:
        embeddings = build_embedding_client(settings.LLM)
        count = process_pdf_file(material, embedding_client=embeddings)
        material.processing_error = ""
        material.save(update_fields=["processing_error"])
        return {"chunks": count}
    except PDFProcessingError as exc:
        # A page-limit or corrupt-file error is deterministic: retrying the
        # same file will fail again the same way. Record the reason instead
        # of burning 3 retries, so the instructor actually sees why the
        # material was never embedded (previously this left embedding_status
        # stuck at False with no explanation anywhere).
        logger.warning("PDF %s rejected: %s", material_id, exc)
        material.processing_error = str(exc)
        material.embedding_status = False
        material.save(update_fields=["processing_error", "embedding_status"])
        raise
    except Exception as exc:
        logger.exception("Transient error processing PDF %s", material_id)
        material.processing_error = f"Временная ошибка обработки, повтор попытки: {exc}"
        material.save(update_fields=["processing_error"])
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
