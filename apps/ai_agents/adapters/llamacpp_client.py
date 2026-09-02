from __future__ import annotations

from typing import Any

from apps.common.exceptions import AIGenerationError, LLMNotConfiguredError
from apps.common.interfaces import AIClientProtocol


class LlamaCppPythonClient(AIClientProtocol):
    """In-process GGUF via `llama-cpp-python` (optional extra)."""

    def __init__(
        self,
        *,
        model_path: str,
        n_ctx: int = 8192,
        n_gpu_layers: int = 0,
        n_threads: int | None = None,
        chat_format: str = "chatml",
    ) -> None:
        if not model_path:
            raise LLMNotConfiguredError(
                "LLAMA_CPP_MODEL_PATH is required for LLM_PROVIDER=llamacpp_python"
            )
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise LLMNotConfiguredError(
                "Install llama-cpp-python to use in-process GGUF models: "
                "pip install llama-cpp-python"
            ) from exc

        kwargs: dict[str, Any] = {
            "model_path": model_path,
            "n_ctx": n_ctx,
            "n_gpu_layers": n_gpu_layers,
            "chat_format": chat_format,
            "verbose": False,
        }
        if n_threads is not None:
            kwargs["n_threads"] = n_threads
        self._llm = Llama(**kwargs)

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        timeout: float | None = None,
    ) -> str:
        del timeout  # llama-cpp-python does not expose a request timeout
        result = self._llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You return only valid JSON. No markdown, no commentary.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        message = result["choices"][0]["message"]["content"]
        if not message:
            raise AIGenerationError("Empty llama.cpp response")
        return str(message)
