from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.common.interfaces import BlockType


class CourseSpec(BaseModel):
    discipline_name: str
    education_direction: str
    course_hours: int = Field(ge=1)


class SectionInput(BaseModel):
    title: str
    description: str = ""
    hours: int = Field(ge=0)
    objectives: list[str] = Field(default_factory=list)


class StructureOutput(BaseModel):
    sections: list[SectionInput]


class SourceReference(BaseModel):
    model_config = ConfigDict(extra="allow")

    filename: str | None = None
    chunk: str | None = None


class BlockOutput(BaseModel):
    type: BlockType
    content: dict[str, Any] = Field(default_factory=dict)
    source_reference: dict[str, Any] | None = None
    version: int = Field(default=1, ge=1)

    @field_validator("type", mode="before")
    @classmethod
    def coerce_type(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            aliases = {
                "презентация": BlockType.PRESENTATION.value,
                "теория": BlockType.THEORY.value,
                "вопрос": BlockType.QUIZ.value,
                "самопроверка": BlockType.QUIZ.value,
                "quiz": BlockType.QUIZ.value,
                "тест": BlockType.TEST.value,
            }
            return aliases.get(normalized, normalized)
        return value
