from __future__ import annotations

import uuid

from django.db import models

from apps.courses.models import Course


class UserMaterial(models.Model):
    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course: models.ForeignKey = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    filename: models.CharField = models.CharField(max_length=255)
    filepath: models.FileField = models.FileField(upload_to="uploads/%Y/%m/%d/")
    filetype: models.CharField = models.CharField(max_length=10, default="pdf")
    embedding_status: models.BooleanField = models.BooleanField(default=False)
    page_count: models.PositiveIntegerField = models.PositiveIntegerField(default=0)
    uploaded_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.filename


class MaterialEmbedding(models.Model):
    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    material: models.ForeignKey = models.ForeignKey(
        UserMaterial,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_text: models.TextField = models.TextField()
    embedding_vector: models.JSONField = models.JSONField(default=list)
    chunk_metadata: models.JSONField = models.JSONField(default=dict)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]   