from __future__ import annotations

from django.apps import AppConfig


class EditorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.editor"
    verbose_name = "Редактор"
