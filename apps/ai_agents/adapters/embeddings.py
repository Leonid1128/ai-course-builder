from __future__ import annotations

from openai import OpenAI

from apps.common.exceptions import LLMNotConfiguredError
from apps.common.interfaces import EmbeddingClientProtocol
from core.llm_config import LLMConfig


class OpenAICompatibleEmbeddings(EmbeddingClientProtocol):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        timeout: float = 60.0,          
        batch_size: int = 20,           
        max_retries: int = 3,           
    ) -> None:
        kwargs: dict[str, object] = {
            "api_key": api_key or "sk-local",
            "timeout": timeout,
            "max_retries": max_retries,
        }
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)
        self._model = model
        self._batch_size = batch_size

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        all_embeddings: list[tuple[int, list[float]]] = []

        for i in range(0, len(texts), self._batch_size):
            batch = texts[i:i + self._batch_size]
            response = self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            for item in response.data:
                all_embeddings.append((item.index, list(item.embedding)))

        all_embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in all_embeddings]


class LlamaCppPythonEmbeddings(EmbeddingClientProtocol):
    def __init__(self, *, model_path: str, n_ctx: int = 8192) -> None:
        if not model_path:
            raise LLMNotConfiguredError("LLAMA_CPP_MODEL_PATH is required for embeddings")
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise LLMNotConfiguredError("Install llama-cpp-python for local embeddings") from exc
        self._llm = Llama(model_path=model_path, embedding=True, n_ctx=n_ctx, verbose=False)

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            raw = self._llm.create_embedding(text)
            vectors.append(list(raw["data"][0]["embedding"]))
        return vectors


def build_embedding_client(config: LLMConfig) -> EmbeddingClientProtocol | None:
    """Return None when embeddings are unavailable; RAG then uses lexical search."""
    if config.provider == "llamacpp_python":
        if not config.llama_model_path:
            return None
        try:
            return LlamaCppPythonEmbeddings(
                model_path=config.llama_model_path,
                n_ctx=config.n_ctx,
            )
        except LLMNotConfiguredError:
            return None
    if config.provider == "openai" and not config.api_key:
        return None
    try:
        return OpenAICompatibleEmbeddings(
            api_key=config.api_key,
            model=config.embedding_model,
            base_url=config.base_url,
            timeout=config.block_timeout,
        )
    except Exception:
        return None
