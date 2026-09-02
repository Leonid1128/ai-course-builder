from __future__ import annotations


class AIGenerationError(Exception):
    """Raised when an LLM call or its payload cannot be used."""


class InvalidJSONError(AIGenerationError):
    """Raised when the model did not return parseable JSON."""


class LLMNotConfiguredError(AIGenerationError):
    """Raised when the selected LLM backend is missing config or extras."""


class PDFProcessingError(Exception):
    """Raised when a PDF cannot be ingested (including the 100-page limit)."""
