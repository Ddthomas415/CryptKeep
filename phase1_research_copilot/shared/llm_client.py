from __future__ import annotations

from typing import Any

from shared.config import Settings, get_settings
from shared.logging import configure_logging


class OpenAIResponsesClient:
    """Small Responses API wrapper so OpenAI integration stays isolated."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.logger = configure_logging("openai-responses-client", self.settings.log_level)
        self._client: Any | None = None

    @property
    def enabled(self) -> bool:
        return bool(str(self.settings.openai_api_key or "").strip())

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self.enabled:
            raise RuntimeError("openai_api_key_missing")

        try:
            from openai import AsyncOpenAI
        except Exception as exc:  # pragma: no cover - exercised via runtime fallback
            raise RuntimeError(f"openai_import_failed:{type(exc).__name__}") from exc

        kwargs: dict[str, Any] = {"api_key": self.settings.openai_api_key}
        base_url = str(self.settings.openai_base_url or "").strip()
        if base_url:
            kwargs["base_url"] = base_url

        self._client = AsyncOpenAI(**kwargs)
        return self._client

    async def create_response(
        self,
        *,
        model: str | None = None,
        input: Any,
        instructions: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        previous_response_id: str | None = None,
        metadata: dict[str, str] | None = None,
        reasoning_effort: str | None = None,
        text_format: dict[str, Any] | None = None,
    ) -> Any:
        request: dict[str, Any] = {
            "model": model or self.settings.openai_model,
            "input": input,
            "store": False,
        }
        if instructions:
            request["instructions"] = instructions
        if tools:
            request["tools"] = tools
        if previous_response_id:
            request["previous_response_id"] = previous_response_id
        if metadata:
            request["metadata"] = metadata
        if reasoning_effort:
            request["reasoning"] = {"effort": reasoning_effort}
        if text_format:
            request["text"] = {"format": text_format}

        client = self._get_client()
        return await client.responses.create(**request)

    @staticmethod
    def output_text(response: Any) -> str:
        text = getattr(response, "output_text", None)
        return text if isinstance(text, str) else ""
