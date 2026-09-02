from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings
from django.db import transaction

from apps.ai_agents.adapters.django_vector_store import DjangoVectorStore
from apps.ai_agents.adapters.embeddings import build_embedding_client
from apps.ai_agents.adapters.factory import build_ai_client
from apps.ai_agents.services.content_generator import ContentBlockGenerator
from apps.ai_agents.services.prompt_builder import FgosPromptBuilder
from apps.ai_agents.services.structure_generator import CourseStructureGenerator
from apps.common.dto import CourseSpec
from apps.courses.models import ContentBlock, Course, CourseSection
from apps.courses.services import record_revision

logger = logging.getLogger(__name__)


def get_structure_generator() -> CourseStructureGenerator:
    return CourseStructureGenerator(build_ai_client(settings.LLM), FgosPromptBuilder())


def get_content_generator() -> ContentBlockGenerator:
    embeddings = build_embedding_client(settings.LLM)
    return ContentBlockGenerator(
        build_ai_client(settings.LLM),
        DjangoVectorStore(embedding_client=embeddings),
        FgosPromptBuilder(),
    )

# soft_time_limit подобрать вручную при использовании локальной llm 

@shared_task(bind=True, max_retries=3, soft_time_limit=45)
def generate_structure_task(self, course_id: str) -> dict[str, str]:
    course = Course.objects.get(id=course_id)
    try:
        generator = get_structure_generator()
        spec = CourseSpec(
            discipline_name=course.discipline_name,
            education_direction=course.education_direction,
            course_hours=course.course_hours,
        )
        sections = generator.generate(spec, timeout=settings.LLM.structure_timeout)
        with transaction.atomic():
            course.sections.all().delete()  # type: ignore[attr-defined]
            for order, sect in enumerate(sections):
                CourseSection.objects.create(
                    course=course,
                    title=sect.title,
                    description=sect.description,
                    hours=sect.hours,
                    objectives=sect.objectives,
                    order=order,
                )
            course.status = Course.Status.READY
            course.last_error = None
            course.save(update_fields=["status", "last_error", "updated_at"])
        return {"status": course.status}
    except Exception as exc:
        logger.exception("Structure generation failed for %s", course_id)
        course.last_error = str(exc)
        if self.request.retries >= self.max_retries:
            course.status = Course.Status.ERROR
        course.save(update_fields=["status", "last_error", "updated_at"])
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# soft_time_limit подобрать вручную при использовании локальной llm 

@shared_task(bind=True, max_retries=3, soft_time_limit=20)
def generate_blocks_for_section(self, section_id: str) -> dict[str, int]:
    section = CourseSection.objects.select_related("course").get(id=section_id)
    try:
        generator = get_content_generator()
        blocks = generator.generate_for_section(
            discipline=section.course.discipline_name,
            section_title=section.title,
            course_id=section.course.id,
            k=settings.RAG_TOP_K,
            timeout=settings.LLM.block_timeout,
        )
        created = 0
        with transaction.atomic():
            section.blocks.all().delete() # type: ignore[attr-defined]
            for order, block in enumerate(blocks):
                ContentBlock.objects.create(
                    section=section,
                    type=block.type.value,
                    content=block.content,
                    source_meta=block.source_reference or {},
                    version=block.version,
                    order=order,
                )
                created += 1
        return {"created": created}
    except Exception as exc:
        logger.exception("Block generation failed for section %s", section_id)
        section.course.last_error = str(exc)
        section.course.save(update_fields=["last_error", "updated_at"])
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

# soft_time_limit подобрать вручную при использовании локальной llm 

@shared_task(bind=True, max_retries=3, soft_time_limit=20)
def regenerate_block_task(self, block_id: str, instruction: str) -> dict[str, int]:
    block = ContentBlock.objects.select_related("section__course").get(id=block_id)
    section = block.section
    try:
        generator = get_content_generator()
        updated = generator.regenerate_block(
            discipline=section.course.discipline_name,
            section_title=section.title,
            course_id=section.course_id,
            block_id=str(block.id),
            block_type=block.type,
            current_content=block.content,
            version=block.version,
            instruction=instruction,
            k=settings.RAG_TOP_K,
            timeout=settings.LLM.block_timeout,
        )
        with transaction.atomic():
            record_revision(block)
            block.content = updated.content
            block.source_meta = updated.source_reference or {}
            block.version = updated.version
            block.save(update_fields=["content", "source_meta", "version", "updated_at"])
        return {"version": block.version}
    except Exception as exc:
        logger.exception("Block regeneration failed for %s", block_id)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
