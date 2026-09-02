from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsInstructorOrReadOnly(BasePermission):
    """Mutations require `X-Instructor-Id` matching `course.instructor_id`."""

    def has_permission(self, request, view) -> bool:  # type: ignore[no-untyped-def]
        if request.method in SAFE_METHODS:
            return True
        return True

    def has_object_permission(self, request, view, obj) -> bool:  # type: ignore[no-untyped-def]
        if request.method in SAFE_METHODS:
            return True
        instructor_id = request.headers.get("X-Instructor-Id")
        if not instructor_id:
            user = getattr(request, "user", None)
            if user is not None and getattr(user, "is_authenticated", False):
                instructor_id = str(user.pk)
        course = obj if hasattr(obj, "instructor_id") else _course_from(obj)
        if course is None:
            return True
        return str(course.instructor_id) == str(instructor_id)


def _course_from(obj):  # type: ignore[no-untyped-def]
    if hasattr(obj, "course"):
        return obj.course
    if hasattr(obj, "section"):
        return obj.section.course
    return None
