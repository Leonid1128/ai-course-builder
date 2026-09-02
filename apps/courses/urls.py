from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.courses.views import BlockViewSet, CourseViewSet, SectionViewSet

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"sections", SectionViewSet, basename="section")
router.register(r"blocks", BlockViewSet, basename="block")

urlpatterns = [
    path("", include(router.urls)),
]
