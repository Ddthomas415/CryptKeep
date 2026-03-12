from __future__ import annotations

import importlib.util
import sys
from argparse import Namespace
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1] / "phase1_research_copilot"
SMOKE_PATH = PHASE1_ROOT / "scripts" / "smoke_phase1_copilot.py"


def _load_smoke_module():
    spec = importlib.util.spec_from_file_location("phase1_smoke_test_module", SMOKE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase1_smoke_test_module"] = module
    spec.loader.exec_module(module)
    return module


def test_summary_is_ok_without_openai_requirement() -> None:
    smoke = _load_smoke_module()
    summary = {
        "gateway_health": {"status": "ok", "openai_enabled": False},
        "orchestrator_health": {"status": "ok", "openai_enabled": False, "no_trading": True},
        "explain": {"status": "ok", "provider": "fallback", "fallback": True, "execution_disabled": True},
        "chat": {
            "status": "ok",
            "provider": "fallback",
            "fallback": True,
            "execution_disabled": True,
            "assistant_response": "Fallback answer.",
            "reasoning_summary": "Explain: Gateway Fallback | fallback\nChat: Fallback | fallback",
        },
    }

    assert smoke._summary_is_ok(summary, expect_openai=False) is True


def test_summary_is_ok_requires_openai_when_requested() -> None:
    smoke = _load_smoke_module()
    summary = {
        "gateway_health": {"status": "ok", "openai_enabled": True},
        "orchestrator_health": {"status": "ok", "openai_enabled": True, "no_trading": True},
        "explain": {"status": "ok", "provider": "openai", "fallback": False, "execution_disabled": True},
        "chat": {
            "status": "ok",
            "provider": "openai",
            "fallback": False,
            "execution_disabled": True,
            "assistant_response": "OpenAI answer.",
            "reasoning_summary": "Explain: OpenAI | gpt-4.1-mini\nChat: OpenAI | gpt-4.1-mini",
        },
    }

    assert smoke._summary_is_ok(summary, expect_openai=True) is True


def test_summary_is_not_ok_when_openai_expected_but_fallback_used() -> None:
    smoke = _load_smoke_module()
    summary = {
        "gateway_health": {"status": "ok", "openai_enabled": True},
        "orchestrator_health": {"status": "ok", "openai_enabled": True, "no_trading": True},
        "explain": {"status": "ok", "provider": "fallback", "fallback": True, "execution_disabled": True},
        "chat": {
            "status": "ok",
            "provider": "openai",
            "fallback": False,
            "execution_disabled": True,
            "assistant_response": "OpenAI answer.",
            "reasoning_summary": "Explain: Fallback | fallback\nChat: OpenAI | gpt-4.1-mini",
        },
    }

    assert smoke._summary_is_ok(summary, expect_openai=True) is False


def test_summary_is_not_ok_when_research_only_boundary_breaks() -> None:
    smoke = _load_smoke_module()
    summary = {
        "gateway_health": {"status": "ok", "openai_enabled": True},
        "orchestrator_health": {"status": "ok", "openai_enabled": True, "no_trading": False},
        "explain": {"status": "ok", "provider": "openai", "fallback": False, "execution_disabled": False},
        "chat": {
            "status": "ok",
            "provider": "openai",
            "fallback": False,
            "execution_disabled": False,
            "assistant_response": "Unsafe answer.",
            "reasoning_summary": "Explain: OpenAI | gpt-4.1-mini\nChat: OpenAI | gpt-4.1-mini",
        },
    }

    assert smoke._summary_is_ok(summary, expect_openai=True) is False


def test_summary_is_not_ok_when_chat_reasoning_summary_is_missing() -> None:
    smoke = _load_smoke_module()
    summary = {
        "gateway_health": {"status": "ok", "openai_enabled": False},
        "orchestrator_health": {"status": "ok", "openai_enabled": False, "no_trading": True},
        "explain": {"status": "ok", "provider": "fallback", "fallback": True, "execution_disabled": True},
        "chat": {
            "status": "ok",
            "provider": "fallback",
            "fallback": True,
            "execution_disabled": True,
            "assistant_response": "Fallback answer.",
            "reasoning_summary": "",
        },
    }

    assert smoke._summary_is_ok(summary, expect_openai=False) is False


def test_build_summary_collects_phase1_endpoints() -> None:
    smoke = _load_smoke_module()
    seen: list[tuple[str, str]] = []

    def fake_request_json(url: str, *, method: str = "GET", payload=None, timeout: float = 5.0):
        seen.append((method, url))
        if url.endswith("/healthz") and ":8001" in url:
            return {"ok": True, "openai_enabled": True}
        if url.endswith("/healthz") and ":8002" in url:
            return {"ok": True, "openai_enabled": True, "no_trading": True}
        if url.endswith("/v1/explain"):
            return {
                "assistant_status": {"provider": "openai", "fallback": False},
                "confidence": 0.73,
                "execution_disabled": True,
                "current_cause": "Tool-grounded cause",
            }
        if url.endswith("/v1/chat"):
            return {
                "chat_status": {"provider": "openai", "fallback": False},
                "assistant_response": "Concise research answer.",
                "reasoning_summary": "Explain: OpenAI | gpt-4.1-mini\nChat: OpenAI | gpt-4.1-mini",
                "execution_disabled": True,
            }
        raise AssertionError(f"unexpected url: {url}")

    args = Namespace(
        gateway_url="http://localhost:8001",
        orchestrator_url="http://localhost:8002",
        asset="SOL",
        question="Why is SOL moving?",
        lookback_minutes=60,
        timeout=5.0,
        expect_openai=True,
    )

    summary = smoke._build_summary(args, request_json=fake_request_json)

    assert [item[1] for item in seen] == [
        "http://localhost:8001/healthz",
        "http://localhost:8002/healthz",
        "http://localhost:8002/v1/explain",
        "http://localhost:8001/v1/chat",
    ]
    assert summary["explain"]["provider"] == "openai"
    assert summary["chat"]["assistant_response"] == "Concise research answer."
    assert summary["chat"]["reasoning_summary"].startswith("Explain: OpenAI")
