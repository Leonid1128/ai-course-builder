from __future__ import annotations

from django.urls import path

from apps.editor.views import editor_page, health, llm_status, task_status

urlpatterns = [
    path("", editor_page, name="editor"),
    path("api/health/", health, name="health"),
    path("api/llm/", llm_status, name="llm-status"),
    path("api/tasks/<str:task_id>/", task_status, name="task-status"),
]
