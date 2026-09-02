from __future__ import annotations

from apps.common.exceptions import LLMNotConfiguredError
from apps.common.interfaces import AIClientProtocol
from apps.ai_agents.adapters.llamacpp_client import LlamaCppPythonClient
from apps.ai_agents.adapters.openai_client import OpenAICompatibleClient
from core.llm_config import LLMConfig


def build_ai_client(config: LLMConfig) -> AIClientProtocol:
    if config.provider == "llamacpp_python":
        if not config.llama_model_path:
            raise LLMNotConfiguredError("Set LLAMA_CPP_MODEL_PATH to a .gguf file")
        return LlamaCppPythonClient(
            model_path=config.llama_model_path,
            n_ctx=config.n_ctx,
            n_gpu_layers=config.n_gpu_layers,
            n_threads=config.n_threads,
            chat_format=config.chat_format,
        )

    if config.provider == "openai" and not config.api_key:
        raise LLMNotConfiguredError("OPENAI_API_KEY (or LLM_API_KEY) is not set")

    return OpenAICompatibleClient(
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url,
        timeout=max(config.structure_timeout, config.block_timeout),
    )
