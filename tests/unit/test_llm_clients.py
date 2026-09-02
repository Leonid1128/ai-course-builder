from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from apps.ai_agents.adapters.factory import build_ai_client
from apps.ai_agents.adapters.llamacpp_client import LlamaCppPythonClient
from apps.common.exceptions import LLMNotConfiguredError
from core.llm_config import LLMConfig, load_llm_config


def _config(**overrides: object) -> LLMConfig:
    base = LLMConfig(
        provider="openai",
        api_key="sk-test",
        model="gpt-4o-mini",
        embedding_model="text-embedding-3-small",
        base_url=None,
        structure_timeout=30.0,
        block_timeout=10.0,
        temperature=0.3,
        llama_model_path=None,
        n_ctx=8192,
        n_gpu_layers=0,
        n_threads=None,
        chat_format="chatml",
    )
    return LLMConfig(**{**base.__dict__, **overrides})


def test_load_llm_config_llamacpp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "llamacpp")
    monkeypatch.setenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1")
    monkeypatch.setenv("LLM_MODEL", "qwen2.5-7b")
    config = load_llm_config()
    assert config.provider == "llamacpp"
    assert config.is_local
    assert config.base_url == "http://127.0.0.1:8080/v1"
    assert config.model == "qwen2.5-7b"


def test_load_llm_config_rejects_unknown_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "watson")
    with pytest.raises(ValueError):
        load_llm_config()


def test_factory_openai_compatible_for_llamacpp_server() -> None:
    client = build_ai_client(_config(provider="llamacpp", base_url="http://localhost:8080/v1", api_key="sk-local"))
    assert client.__class__.__name__ == "OpenAICompatibleClient"


def test_factory_requires_gguf_path() -> None:
    with pytest.raises(LLMNotConfiguredError):
        build_ai_client(_config(provider="llamacpp_python", llama_model_path=None))


def test_llamacpp_python_client_generate() -> None:
    fake_llm = MagicMock()
    fake_llm.create_chat_completion.return_value = {
        "choices": [{"message": {"content": '{"ok": true}'}}]
    }
    with patch.object(LlamaCppPythonClient, "__init__", lambda self, **kwargs: None):
        client = LlamaCppPythonClient(model_path="unused.gguf")
        client._llm = fake_llm
        assert client.generate("hello") == '{"ok": true}'
