from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.ai_agents.tasks import (
    generate_blocks_for_section,
    generate_structure_task,
    regenerate_block_task,
)
from apps.courses.models import ContentBlock, Course, CourseSection
from apps.courses.permissions import IsInstructorOrReadOnly
from apps.courses.serializers import (
    BlockRevisionSerializer,
    BlockSerializer,
    BulkIdsSerializer,
    CourseDetailSerializer,
    CourseSerializer,
    RegenerateSerializer,
    ReorderItemSerializer,
    SectionSerializer,
)
from apps.courses.services import record_revision, reorder_blocks


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.prefetch_related("sections__blocks", "materials").all()
    permission_classes = [IsInstructorOrReadOnly]

    def get_serializer_class(self) -> type[CourseSerializer]:
        if self.action in {"retrieve", "generate_structure", "generate_all_blocks"}:
            return CourseDetailSerializer
        return CourseSerializer

    @action(detail=True, methods=["post"], url_path="generate-structure")
    def generate_structure(self, request: Request, pk: str | None = None) -> Response:
        course = self.get_object()
        if course.status == Course.Status.GENERATING:
            return Response(
                {"error": "Already generating"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        course.status = Course.Status.GENERATING
        course.last_error = None
        course.save(update_fields=["status", "last_error", "updated_at"])
        task = generate_structure_task.delay(str(course.id))
        return Response({"task_id": task.id, "status": course.status})

    @action(detail=True, methods=["post"], url_path="generate-all-blocks")
    def generate_all_blocks(self, request: Request, pk: str | None = None) -> Response:
        course = self.get_object()
        if course.status != Course.Status.READY:
            return Response(
                {"error": "Course structure not ready"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        task_ids = [
            generate_blocks_for_section.delay(str(section.id)).id
            for section in course.sections.all()
        ]
        return Response({"task_ids": task_ids, "count": len(task_ids)})

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request: Request, pk: str | None = None) -> Response:
        course = self.get_object()
        return Response(CourseDetailSerializer(course).data)


class SectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CourseSection.objects.select_related("course").prefetch_related("blocks")
    serializer_class = SectionSerializer

    @action(detail=True, methods=["post"], url_path="generate-blocks")
    def generate_blocks(self, request: Request, pk: str | None = None) -> Response:
        section = self.get_object()
        task = generate_blocks_for_section.delay(str(section.id))
        return Response({"task_id": task.id})


class BlockViewSet(viewsets.ModelViewSet):
    queryset = ContentBlock.objects.select_related("section__course").all()
    serializer_class = BlockSerializer
    permission_classes = [IsInstructorOrReadOnly]

    def perform_update(self, serializer: BlockSerializer) -> None: # type: ignore[override]
        block: ContentBlock = serializer.instance # type: ignore[assignment]
        record_revision(block)
        block.bump_version()
        serializer.save(version=block.version)

    @action(detail=True, methods=["post"])
    def regenerate(self, request: Request, pk: str | None = None) -> Response:
        block = self.get_object()
        payload = RegenerateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        instruction = payload.validated_data.get("instruction") or "Улучши качество контента"
        task = regenerate_block_task.delay(str(block.id), instruction)
        return Response({"task_id": task.id})

    @action(detail=True, methods=["get"])
    def history(self, request: Request, pk: str | None = None) -> Response:
        block = self.get_object()
        revisions = block.revisions.all()
        return Response(BlockRevisionSerializer(revisions, many=True).data)

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request: Request) -> Response:
        serializer = ReorderItemSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        reorder_blocks(serializer.validated_data)
        return Response({"status": "ok"})

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request: Request) -> Response:
        serializer = BulkIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        deleted, _ = ContentBlock.objects.filter(id__in=ids).delete()
        return Response({"deleted": deleted})

    @action(detail=True, methods=["post"], url_path="restore/(?P<revision_id>[^/.]+)")
    def restore(self, request: Request, pk: str | None = None, revision_id: str | None = None) -> Response:
        block = self.get_object()
        revision = get_object_or_404(block.revisions, id=revision_id)
        with transaction.atomic():
            record_revision(block)
            block.content = revision.content
            block.source_meta = revision.source_meta
            block.bump_version()
            block.save(update_fields=["content", "source_meta", "version", "updated_at"])
        return Response(BlockSerializer(block).data)
