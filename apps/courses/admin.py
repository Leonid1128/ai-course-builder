from django.contrib import admin

from apps.courses.models import BlockRevision, ContentBlock, Course, CourseSection


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("discipline_name", "instructor_fio", "status", "course_hours", "updated_at")
    list_filter = ("status",)
    search_fields = ("discipline_name", "instructor_fio", "instructor_id")


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "hours", "order")


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ("type", "section", "version", "order")
    list_filter = ("type",)


@admin.register(BlockRevision)
class BlockRevisionAdmin(admin.ModelAdmin):
    list_display = ("block", "version", "created_at")
