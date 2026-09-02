from __future__ import annotations

import json
import re
from typing import Any

from apps.common.exceptions import InvalidJSONError

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)


def extract_json_text(raw: str) -> str:
    text = raw.strip()
    fenced = _FENCE_RE.search(text)
    if fenced:
        return fenced.group(1).strip()

    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end > start:
            return text[start : end + 1]
    return text


def parse_llm_json(raw: str) -> Any:
    candidate = extract_json_text(raw)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise InvalidJSONError(f"AI returned malformed JSON: {exc}") from exc
