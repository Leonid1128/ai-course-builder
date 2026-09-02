from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.courses.models import Course


@pytest.mark.django_db
def test_generate_structure_api(api_client, course, instructor_id):
    url = reverse("course-generate-structure", kwargs={"pk": course.id})
    with patch("apps.courses.views.generate_structure_task.delay") as mock_task:
        mock_task.return_value.id = "task123"
        response = api_client.post(url, HTTP_X_INSTRUCTOR_ID=instructor_id)
    assert response.status_code == 200
    assert response.data["task_id"] == "task123"
    course.refresh_from_db()
    assert course.status == Course.Status.GENERATING


@pytest.mark.django_db
def test_generate_structure_fails_if_generating(api_client, course, instructor_id):
    course.status = Course.Status.GENERATING
    course.save()
    url = reverse("course-generate-structure", kwargs={"pk": course.id})
    response = api_client.post(url, HTTP_X_INSTRUCTOR_ID=instructor_id)
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_course(api_client, instructor_id):
    response = api_client.post(
        reverse("course-list"),
        {
            "instructor_id": instructor_id,
            "instructor_fio": "Петров П.П.",
            "discipline_name": "Алгебра",
            "education_direction": "01.03.01",
            "course_hours": 72,
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["status"] == Course.Status.DRAFT


@pytest.mark.django_db
def test_block_manual_edit_bumps_version(api_client, block, instructor_id):
    url = reverse("block-detail", kwargs={"pk": block.id})
    response = api_client.patch(
        url,
        {"content": {"text": "новая редакция"}},
        format="json",
        HTTP_X_INSTRUCTOR_ID=instructor_id,
    )
    assert response.status_code == 200
    assert response.data["version"] == 2
    assert block.revisions.count() == 1


@pytest.mark.django_db
def test_reorder_and_bulk_delete(api_client, section, instructor_id):
    from apps.courses.factories import BlockFactory

    first = BlockFactory(section=section, order=0)
    second = BlockFactory(section=section, order=1)
    reorder_url = reverse("block-reorder")
    response = api_client.post(
        reorder_url,
        [{"id": str(first.id), "order": 5}, {"id": str(second.id), "order": 1}],
        format="json",
        HTTP_X_INSTRUCTOR_ID=instructor_id,
    )
    assert response.status_code == 200
    first.refresh_from_db()
    second.refresh_from_db()
    assert first.order == 5
    assert second.order == 1

    delete_url = reverse("block-bulk-delete")
    response = api_client.post(
        delete_url,
        {"ids": [str(first.id)]},
        format="json",
        HTTP_X_INSTRUCTOR_ID=instructor_id,
    )
    assert response.status_code == 200
    assert response.data["deleted"] >= 1


@pytest.mark.django_db
def test_health_and_llm_status(api_client):
    health = api_client.get("/api/health/")
    assert health.status_code == 200
    llm = api_client.get("/api/llm/")
    assert llm.status_code == 200
    assert "provider" in llm.data
