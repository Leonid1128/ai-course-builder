from __future__ import annotations

import logging

from apps.common.dto import CourseSpec, SectionInput, StructureOutput
from apps.common.exceptions import InvalidJSONError
from apps.common.interfaces import AIClientProtocol, PromptBuilderProtocol
from apps.common.json_utils import parse_llm_json

logger = logging.getLogger(__name__)


class CourseStructureGenerator:
    def __init__(self, ai_client: AIClientProtocol, prompt_builder: PromptBuilderProtocol) -> None:
        self.ai_client = ai_client
        self.prompt_builder = prompt_builder

    def generate(self, course: CourseSpec, *, timeout: float = 30.0) -> list[SectionInput]:
        prompt = self.prompt_builder.build_structure_prompt(
            discipline=course.discipline_name,
            direction=course.education_direction,
            hours=course.course_hours,
        )
        raw = self.ai_client.generate(prompt, timeout=timeout)
        payload = parse_llm_json(raw)
        if isinstance(payload, list):
            payload = {"sections": payload}
        try:
            parsed = StructureOutput.model_validate(payload)
        except Exception as exc:
            logger.error("Structure schema mismatch: %s", payload)
            raise InvalidJSONError("AI returned JSON that does not match the structure schema") from exc
        return parsed.sections
