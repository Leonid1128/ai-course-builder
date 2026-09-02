from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

LLMProvider = Literal["openai", "llamacpp", "llamacpp_python"]


def _env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None else value


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    return default if raw is None or raw == "" else float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    return default if raw is None or raw == "" else int(raw)


@dataclass(frozen=True)
class LLMConfig:
    """Runtime LLM settings. llama.cpp server is OpenAI-compatible (`/v1`)."""

    provider: LLMProvider
    api_key: str
    model: str
    embedding_model: str
    base_url: str | None
    structure_timeout: float
    block_timeout: float
    temperature: float
    llama_model_path: str | None
    n_ctx: int
    n_gpu_layers: int
    n_threads: int | None
    chat_format: str

    @property
    def is_local(self) -> bool:
        return self.provider in {"llamacpp", "llamacpp_python"}


def load_llm_config() -> LLMConfig:
    provider_raw = _env("LLM_PROVIDER", "openai").strip().lower().replace("-", "_")
    if provider_raw not in {"openai", "llamacpp", "llamacpp_python"}:
        raise ValueError(
            f"Unknown LLM_PROVIDER={provider_raw!r}. "
            "Use openai, llamacpp, or llamacpp_python."
        )
    provider: LLMProvider = provider_raw  # type: ignore[assignment]

    default_base: str | None
    default_key: str
    default_model: str
    if provider == "openai":
        default_base = None
        default_key = _env("OPENAI_API_KEY")
        default_model = "gpt-4o-mini"
    elif provider == "llamacpp":
        default_base = "http://127.0.0.1:8080/v1"
        default_key = "sk-local"
        default_model = "local-model"
    else:
        default_base = None
        default_key = "sk-local"
        default_model = "local-model"

    base_url = _env("LLM_BASE_URL", default_base or "") or default_base
    model_path = _env("LLAMA_CPP_MODEL_PATH") or None
    threads_raw = os.getenv("LLAMA_CPP_N_THREADS")

    return LLMConfig(
        provider=provider,
        api_key=_env("LLM_API_KEY") or default_key,
        model=_env("LLM_MODEL", default_model),
        embedding_model=_env("LLM_EMBEDDING_MODEL", "text-embedding-3-small"),
        base_url=base_url,
        structure_timeout=_env_float("LLM_STRUCTURE_TIMEOUT", 30.0),
        block_timeout=_env_float("LLM_BLOCK_TIMEOUT", 10.0),
        temperature=_env_float("LLM_TEMPERATURE", 0.3),
        llama_model_path=model_path,
        n_ctx=_env_int("LLAMA_CPP_N_CTX", 8192),
        n_gpu_layers=_env_int("LLAMA_CPP_N_GPU_LAYERS", 0),
        n_threads=int(threads_raw) if threads_raw else None,
        chat_format=_env("LLAMA_CPP_CHAT_FORMAT", "chatml"),
    )
