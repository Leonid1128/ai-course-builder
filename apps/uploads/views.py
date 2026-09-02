from __future__ import annotations

from rest_framework import mixins, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response

from apps.uploads.models import UserMaterial
from apps.uploads.serializers import UploadMaterialSerializer
from apps.uploads.tasks import process_pdf_task


class MaterialViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = UserMaterial.objects.select_related("course").all()
    serializer_class = UploadMaterialSerializer
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        material = serializer.save()
        task = process_pdf_task.delay(str(material.id))
        payload = serializer.data
        payload["task_id"] = task.id
        return Response(payload, status=status.HTTP_201_CREATED)
