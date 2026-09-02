from __future__ import annotations

from rest_framework import serializers

from apps.courses.models import BlockRevision, ContentBlock, Course, CourseSection
from apps.uploads.models import UserMaterial


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentBlock
        fields = [
            "id",
            "section",
            "type",
            "content",
            "source_meta",
            "version",
            "order",
            "updated_at",
        ]
        read_only_fields = ["id", "version", "updated_at"]


class BlockRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockRevision
        fields = ["id", "version", "content", "source_meta", "created_at"]


class SectionSerializer(serializers.ModelSerializer):
    blocks = BlockSerializer(many=True, read_only=True)

    class Meta:
        model = CourseSection
        fields = [
            "id",
            "course",
            "title",
            "description",
            "hours",
            "objectives",
            "order",
            "blocks",
        ]
        read_only_fields = ["id"]


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMaterial
        fields = [
            "id",
            "filename",
            "filepath",
            "filetype",
            "embedding_status",
            "uploaded_at",
        ]
        read_only_fields = ["id", "filename", "filetype", "embedding_status", "uploaded_at"]


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "instructor_id",
            "instructor_fio",
            "discipline_name",
            "education_direction",
            "course_hours",
            "status",
            "last_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "last_error", "created_at", "updated_at"]


class CourseDetailSerializer(CourseSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    materials = MaterialSerializer(many=True, read_only=True)

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ["sections", "materials"]


class ReorderItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    order = serializers.IntegerField(min_value=0)


class BulkIdsSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)


class RegenerateSerializer(serializers.Serializer):
    instruction = serializers.CharField(required=False, allow_blank=True, default="")
