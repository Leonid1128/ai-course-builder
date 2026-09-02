from __future__ import annotations

from unittest.mock import Mock
from uuid import UUID

import pytest

from apps.ai_agents.services.content_generator import ContentBlockGenerator
from apps.ai_agents.services.structure_generator import CourseStructureGenerator
from apps.common.dto import CourseSpec
from apps.common.exceptions import InvalidJSONError


def test_structure_generator_returns_sections() -> None:
    mock_ai = Mock()
    mock_ai.generate.return_value = (
        '{"sections": [{"title": "Intro", "description": "desc", "hours": 2, "objectives": []}]}'
    )
    mock_builder = Mock()
    mock_builder.build_structure_prompt.return_value = "prompt"
    generator = CourseStructureGenerator(mock_ai, mock_builder)
    result = generator.generate(
        CourseSpec(discipline_name="CS", education_direction="09.03.01", course_hours=36)
    )
    assert len(result) == 1
    assert result[0].title == "Intro"
    mock_ai.generate.assert_called_once()


def test_structure_generator_accepts_bare_array() -> None:
    mock_ai = Mock()
    mock_ai.generate.return_value = '```json\n[{"title": "A", "hours": 1}]\n```'
    mock_builder = Mock()
    mock_builder.build_structure_prompt.return_value = "prompt"
    generator = CourseStructureGenerator(mock_ai, mock_builder)
    result = generator.generate(
        CourseSpec(discipline_name="CS", education_direction="09.03.01", course_hours=36)
    )
    assert result[0].title == "A"


def test_structure_generator_rejects_bad_json() -> None:
    mock_ai = Mock()
    mock_ai.generate.return_value = "oops"
    mock_builder = Mock()
    mock_builder.build_structure_prompt.return_value = "prompt"
    generator = CourseStructureGenerator(mock_ai, mock_builder)
    with pytest.raises(InvalidJSONError):
        generator.generate(
            CourseSpec(discipline_name="CS", education_direction="09.03.01", course_hours=36)
        )


def test_content_generator_uses_vector_store() -> None:
    mock_ai = Mock()
    mock_ai.generate.return_value = (
        '[{"block_id": "123e4567-e89b-12d3-a456-426614174000",'
        ' "type": "theory", "content": {"text": "ok"}, "source_reference": {}}]'
    )
    mock_vector = Mock()
    mock_vector.similarity_search.return_value = [
        {"text": "context", "metadata": {"filename": "lec.pdf"}}
    ]
    mock_builder = Mock()
    mock_builder.build_content_prompt.return_value = "prompt"
    generator = ContentBlockGenerator(mock_ai, mock_vector, mock_builder)
    course_id = UUID("123e4567-e89b-12d3-a456-426614174111")
    result = generator.generate_for_section(
        discipline="CS",
        section_title="Intro",
        course_id=course_id,
    )
    assert len(result) == 1
    assert result[0].type.value == "theory"
    mock_vector.similarity_search.assert_called_once()
    kwargs = mock_vector.similarity_search.call_args
    assert kwargs.kwargs["course_id"] == course_id


def test_regenerate_increments_version() -> None:
    mock_ai = Mock()
    mock_ai.generate.return_value = (
        '{"block_id": "123e4567-e89b-12d3-a456-426614174000",'
        ' "type": "quiz", "content": {"q": "1+1?"}, "version": 1}'
    )
    mock_vector = Mock()
    mock_vector.similarity_search.return_value = []
    mock_builder = Mock()
    mock_builder.build_regenerate_prompt.return_value = "prompt"
    generator = ContentBlockGenerator(mock_ai, mock_vector, mock_builder)
    result = generator.regenerate_block(
        discipline="CS",
        section_title="Intro",
        course_id="course-1",
        block_id="123e4567-e89b-12d3-a456-426614174000",
        block_type="quiz",
        current_content={"q": "old"},
        version=4,
        instruction="упрости",
    )
    assert result.version == 5
    assert result.type.value == "quiz"
