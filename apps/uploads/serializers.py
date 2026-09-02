from __future__ import annotations

from rest_framework import serializers

from apps.uploads.models import UserMaterial


class UploadMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMaterial
        fields = [
            "id",
            "course",
            "filepath",
            "filename",
            "filetype",
            "embedding_status",
            "page_count",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "filename",
            "filetype",
            "embedding_status",
            "page_count",
            "uploaded_at",
        ]

    def validate_filepath(self, value):  # type: ignore[no-untyped-def]
        name = getattr(value, "name", "")
        if not str(name).lower().endswith(".pdf"):
            raise serializers.ValidationError("Only PDF files are supported.")
        return value

    def create(self, validated_data: dict) -> UserMaterial:  # type: ignore[type-arg]
        upload = validated_data["filepath"]
        filename = getattr(upload, "name", "material.pdf")
        validated_data["filename"] = filename
        validated_data["filetype"] = "pdf"
        return super().create(validated_data)
