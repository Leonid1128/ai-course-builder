from __future__ import annotations

from celery import shared_task
from django.conf import settings

from apps.ai_agents.adapters.embeddings import build_embedding_client
from apps.uploads.models import UserMaterial
from apps.uploads.services.pdf_processor import process_pdf_file


@shared_task(bind=True, max_retries=3)
def process_pdf_task(self, material_id: str) -> dict[str, int]:
    material = UserMaterial.objects.get(id=material_id)
    try:
        embeddings = build_embedding_client(settings.LLM)
        count = process_pdf_file(material, embedding_client=embeddings)
        return {"chunks": count}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
