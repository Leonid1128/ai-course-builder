from __future__ import annotations

from openai import OpenAI

from apps.common.exceptions import AIGenerationError
from apps.common.interfaces import AIClientProtocol


class OpenAICompatibleClient(AIClientProtocol):
    """Works with OpenAI and llama.cpp `llama-server` (`--api` / `/v1`)."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._client = OpenAI(
            api_key=api_key or "sk-local",
            base_url=base_url, 
            timeout=timeout,
        )
        self._model = model
        self._default_timeout = timeout

    def generate(
        self,
        prompt: str,
        *,
        temperature: float = 0.3,
        timeout: float | None = None,
    ) -> str:
        client = self._client.with_options(timeout=timeout or self._default_timeout)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": "You return only valid JSON. No markdown, no commentary.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        content = response.choices[0].message.content
        if not content:
            raise AIGenerationError("Empty LLM response")
        return content