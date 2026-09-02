from __future__ import annotations

from typing import Any
from uuid import UUID

from apps.common.dto import BlockOutput
from apps.common.exceptions import InvalidJSONError
from apps.common.interfaces import AIClientProtocol, PromptBuilderProtocol, VectorStoreProtocol
from apps.common.json_utils import parse_llm_json


def _format_context(docs: list[dict[str, Any]]) -> str:
    if not docs:
        return "Материалы не загружены. Не выдумывайте факты."
    parts: list[str] = []
    for doc in docs:
        filename = (doc.get("metadata") or {}).get("filename", "")
        prefix = f"[{filename}] " if filename else ""
        parts.append(prefix + doc.get("text", ""))
    return "\n".join(parts)


def _as_block_list(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if "blocks" in payload and isinstance(payload["blocks"], list):
            return payload["blocks"]
        if "type" in payload:
            return [payload]
    raise InvalidJSONError("AI returned JSON that is not a block or a list of blocks")


class ContentBlockGenerator:
    def __init__(
        self,
        ai_client: AIClientProtocol,
        vector_store: VectorStoreProtocol,
        prompt_builder: PromptBuilderProtocol,
    ) -> None:
        self.ai_client = ai_client
        self.vector_store = vector_store
        self.prompt_builder = prompt_builder

    def retrieve_context(self, query: str, course_id: UUID | str, k: int = 5) -> str:
        docs = self.vector_store.similarity_search(query, course_id=course_id, k=k)
        return _format_context(docs)

    def generate_for_section(
        self,
        *,
        discipline: str,
        section_title: str,
        course_id: UUID | str,
        k: int = 5,
        timeout: float = 10.0,
    ) -> list[BlockOutput]:
        context = self.retrieve_context(section_title, course_id, k=k)
        prompt = self.prompt_builder.build_content_prompt(discipline, section_title, context)
        raw = self.ai_client.generate(prompt, timeout=timeout)
        return self._parse_blocks(raw)

    def regenerate_block(
        self,
        *,
        discipline: str,
        section_title: str,
        course_id: UUID | str,
        block_id: str,
        block_type: str,
        current_content: dict[str, Any],
        version: int,
        instruction: str,
        k: int = 5,
        timeout: float = 10.0,
    ) -> BlockOutput:
        context = self.retrieve_context(section_title, course_id, k=k)
        prompt = self.prompt_builder.build_regenerate_prompt(
            discipline=discipline,
            section_title=section_title,
            context=context,
            instruction=instruction,
            block_id=block_id,
            block_type=block_type,
            current_content=current_content,
            version=version,
        )
        raw = self.ai_client.generate(prompt, timeout=timeout)
        blocks = self._parse_blocks(raw)
        block = blocks[0]
        block.version = version + 1
        return block

    def _parse_blocks(self, raw: str) -> list[BlockOutput]:
        payload = parse_llm_json(raw)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"LLM response payload: {payload}") 
        items = _as_block_list(payload)
        try:
            return [BlockOutput.model_validate(item) for item in items]
        except Exception as exc:
            logger.error(f"Failed to validate item: {items}")
            raise InvalidJSONError("AI returned JSON that does not match the block schema") from exc
