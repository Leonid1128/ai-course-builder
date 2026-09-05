from __future__ import annotations

from celery.result import AsyncResult
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response


def editor_page(request):  # type: ignore[no-untyped-def]
    return render(request, "editor/index.html")


@require_GET
def health(_request):  # type: ignore[no-untyped-def]
    return JsonResponse({"status": "ok"})


@api_view(["GET"])
def task_status(_request: Request, task_id: str) -> Response:
    result : AsyncResult = AsyncResult(task_id)
    payload = {"task_id": task_id, "status": result.status, "ready": result.ready()}
    if result.ready():
        if result.successful():
            payload["result"] = result.result
        else:
            payload["error"] = str(result.result)
    return Response(payload)


@api_view(["GET"])
def llm_status(_request: Request) -> Response:
    config = settings.LLM
    return Response(
        {
            "provider": config.provider,
            "model": config.model,
            "base_url": config.base_url,
            "is_local": config.is_local,
            "structure_timeout": config.structure_timeout,
            "block_timeout": config.block_timeout,
        }
    )
