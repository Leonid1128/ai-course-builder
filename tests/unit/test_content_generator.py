from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from apps.ai_agents.services.content_generator import ContentBlockGenerator
from apps.common.exceptions import InvalidJSONError


def _generator(ai_response: str) -> ContentBlockGenerator:
    ai_client = MagicMock()
    ai_client.generate.return_value = ai_response
    vector_store = MagicMock()
    vector_store.similarity_search.return_value = []
    return ContentBlockGenerator(ai_client, vector_store, MagicMock())


def test_regenerate_block_raises_invalid_json_on_empty_ai_response() -> None:
    """Regression test: the AI returning "[]" used to crash with a raw
    IndexError (blocks[0]) instead of the documented InvalidJSONError."""
    generator = _generator("[]")

    with pytest.raises(InvalidJSONError):
        generator.regenerate_block(
            discipline="d",
            section_title="s",
            course_id="11111111-1111-1111-1111-111111111111",
            block_id="b",
            block_type="theory",
            current_content={},
            version=1,
            instruction="x",
        )


def test_regenerate_block_bumps_version_on_success() -> None:
    generator = _generator('{"type": "theory", "content": {"text": "new"}}')

    block = generator.regenerate_block(
        discipline="d",
        section_title="s",
        course_id="11111111-1111-1111-1111-111111111111",
        block_id="b",
        block_type="theory",
        current_content={"text": "old"},
        version=1,
        instruction="x",
    )

    assert block.version == 2
    assert block.content == {"text": "new"}
