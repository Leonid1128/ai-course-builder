from __future__ import annotations

from enum import Enum
from typing import Any, Protocol
from uuid import UUID


class BlockType(str, Enum):
    PRESENTATION = "presentation"
    THEORY = "theory"
    QUIZ = "quiz"
    TEST = "test"


class AIClientProtocol(Protocol):
    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        timeout: float | None = None,
    ) -> str: ...


class EmbeddingClientProtocol(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class VectorStoreProtocol(Protocol):
    def similarity_search(
        self,
        query: str,
        *,
        course_id: UUID | str,
        k: int = 5,
    ) -> list[dict[str, Any]]: ...


class PromptBuilderProtocol(Protocol):
    def build_structure_prompt(self, discipline: str, direction: str, hours: int) -> str: ...

    def build_content_prompt(self, discipline: str, section_title: str, context: str) -> str: ...

    def build_regenerate_prompt(
        self,
        *,
        discipline: str,
        section_title: str,
        context: str,
        instruction: str,
        block_id: str,
        block_type: str,
        current_content: dict[str, Any],
        version: int,
    ) -> str: ...
