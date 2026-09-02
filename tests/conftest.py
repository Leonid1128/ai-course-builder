from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.courses.factories import BlockFactory, CourseFactory, SectionFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def instructor_id() -> str:
    return "instructor-1"


@pytest.fixture
def course(instructor_id: str):
    return CourseFactory(instructor_id=instructor_id)


@pytest.fixture
def section(course):
    return SectionFactory(course=course)


@pytest.fixture
def block(section):
    return BlockFactory(section=section)
