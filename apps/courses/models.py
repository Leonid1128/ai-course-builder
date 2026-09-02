from __future__ import annotations

import uuid
from typing import Any

from django.core.validators import MinValueValidator
from django.db import models


class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Черновик"
        GENERATING = "generating", "Генерация"
        READY = "ready", "Готов"
        ERROR = "error", "Ошибка"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instructor_id = models.CharField(max_length=50, db_index=True)
    instructor_fio = models.CharField(max_length=255)
    discipline_name = models.CharField(max_length=255)
    education_direction = models.CharField(max_length=255)
    course_hours = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    last_error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.discipline_name} ({self.instructor_fio})"


class CourseSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    hours = models.PositiveIntegerField(default=0)
    objectives = models.JSONField(default=list)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self) -> str:
        return self.title


class ContentBlock(models.Model):
    class BlockType(models.TextChoices):
        PRESENTATION = "presentation", "Презентация"
        THEORY = "theory", "Теория"
        QUIZ = "quiz", "Самопроверка"
        TEST = "test", "Тест"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name="blocks",
    )
    type = models.CharField(max_length=20, choices=BlockType.choices)
    content = models.JSONField(default=dict)
    source_meta = models.JSONField(default=dict)
    version = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def bump_version(self) -> None:
        self.version += 1

    def snapshot(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "source_meta": self.source_meta,
            "order": self.order,
        }


class BlockRevision(models.Model):
    """Point-in-time copy of a block for the editor history."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block = models.ForeignKey(
        ContentBlock,
        on_delete=models.CASCADE,
        related_name="revisions",
    )
    version = models.PositiveIntegerField()
    content = models.JSONField(default=dict)
    source_meta = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        unique_together = ("block", "version")
