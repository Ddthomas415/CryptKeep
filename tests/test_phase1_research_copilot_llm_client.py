from __future__ import annotations

import importlib.util
import pytest

if importlib.util.find_spec("phase1_research_copilot.shared.config") is None:
    pytest.skip("phase1_research_copilot.shared.config not present in this repo checkout", allow_module_level=True)


import importlib.util
import pytest

if importlib.util.find_spec("phase1_research_copilot") is None:
    pytest.skip("phase1_research_copilot package not present in this repo checkout", allow_module_level=True)


import asyncio
import sys
from pathlib import Path
from types import ModuleType
from types import SimpleNamespace


PHASE1_ROOT = Path(__file__).resolve().parents[1] / "phase1_research_copilot"
if str(PHASE1_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE1_ROOT))

from phase1_research_copilot.shared.config import Settings  # noqa: E402
from shared.llm_client import OpenAIResponsesClient  # noqa: E402


def test_create_response_builds_expected_responses_request(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _Responses:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text="ok")

    client = OpenAIResponsesClient(Settings(openai_api_key="sk-test", openai_model="gpt-4.1-mini"))
    monkeypatch.setattr(client, "_get_client", lambda: SimpleNamespace(responses=_Responses()))

    response = asyncio.run(
        client.create_response(
            input="hello",
            instructions="Be concise.",
            tools=[{"type": "function", "name": "get_market_snapshot"}],
            previous_response_id="resp_123",
            metadata={"mode": "chat"},
            reasoning_effort="medium",
            text_format={"type": "json_schema", "name": "demo", "schema": {"type": "object"}, "strict": True},
        )
    )

    assert response.output_text == "ok"
    assert captured == {
        "model": "gpt-4.1-mini",
        "input": "hello",
        "store": False,
        "instructions": "Be concise.",
        "tools": [{"type": "function", "name": "get_market_snapshot"}],
        "previous_response_id": "resp_123",
        "metadata": {"mode": "chat"},
        "reasoning": {"effort": "medium"},
        "text": {
            "format": {"type": "json_schema", "name": "demo", "schema": {"type": "object"}, "strict": True}
        },
    }


def test_get_client_uses_base_url_when_configured(monkeypatch) -> None:
    captured: dict[str, object] = {}
    openai_stub = ModuleType("openai")

    class _AsyncOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.responses = SimpleNamespace(create=None)

    openai_stub.AsyncOpenAI = _AsyncOpenAI
    monkeypatch.setitem(sys.modules, "openai", openai_stub)

    client = OpenAIResponsesClient(
        Settings(
            openai_api_key="sk-test",
            openai_base_url="https://example.test/v1",
        )
    )

    instance = client._get_client()

    assert instance is client._client
    assert captured == {
        "api_key": "sk-test",
        "base_url": "https://example.test/v1",
    }


def test_output_text_returns_empty_string_when_missing() -> None:
    assert OpenAIResponsesClient.output_text(SimpleNamespace()) == ""
