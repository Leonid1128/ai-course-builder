from __future__ import annotations

import pytest

from apps.common.exceptions import InvalidJSONError
from apps.common.json_utils import parse_llm_json


def test_parse_fenced_json_object() -> None:
    raw = """Sure.\n```json\n{"sections": [{"title": "A", "hours": 2}]}\n```\n"""
    data = parse_llm_json(raw)
    assert data["sections"][0]["title"] == "A"


def test_parse_json_array_with_prefix() -> None:
    raw = 'Result:\n[{"type": "theory", "content": {}}]'
    data = parse_llm_json(raw)
    assert data[0]["type"] == "theory"


def test_parse_invalid_json() -> None:
    with pytest.raises(InvalidJSONError):
        parse_llm_json("not json at all")
