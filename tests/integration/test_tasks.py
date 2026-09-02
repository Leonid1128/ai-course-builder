from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from apps.ai_agents.tasks import generate_structure_task, regenerate_block_task
from apps.common.dto import BlockOutput, SectionInput
from apps.common.interfaces import BlockType
from apps.courses.factories import BlockFactory, CourseFactory
from apps.courses.models import Course


@pytest.mark.django_db
def test_generate_structure_task_creates_sections():
    course = CourseFactory()
    with patch("apps.ai_agents.tasks.get_structure_generator") as mock_gen_factory:
        mock_gen = Mock()
        mock_gen.generate.return_value = [
            SectionInput(title="Раздел 1", description="desc", hours=2, objectives=[])
        ]
        mock_gen_factory.return_value = mock_gen
        generate_structure_task(str(course.id))
    course.refresh_from_db()
    assert course.status == Course.Status.READY
    assert course.sections.count() == 1


@pytest.mark.django_db
def test_regenerate_block_task_updates_content_and_version():
    block = BlockFactory(version=1, content={"text": "old"})
    with patch("apps.ai_agents.tasks.get_content_generator") as mock_gen_factory:
        mock_gen = Mock()
        mock_gen.regenerate_block.return_value = BlockOutput(
            type=BlockType.THEORY,
            content={"text": "new"},
            source_reference={"filename": "lec.pdf"},
            version=2,
        )
        mock_gen_factory.return_value = mock_gen
        regenerate_block_task(str(block.id), "улучши")
    block.refresh_from_db()
    assert block.content["text"] == "new"
    assert block.version == 2
    assert block.revisions.count() == 1
