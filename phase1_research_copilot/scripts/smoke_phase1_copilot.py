from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


def _request_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None, timeout: float = 5.0) -> dict[str, Any]:
    body: bytes | None = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "Phase1CopilotSmoke/1.0",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _status_label(ok: bool) -> str:
    return "ok" if ok else "error"


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the Phase 1 research copilot gateway and orchestrator.")
    parser.add_argument("--gateway-url", default="http://localhost:8001", help="Gateway base URL.")
    parser.add_argument("--orchestrator-url", default="http://localhost:8002", help="Orchestrator base URL.")
    parser.add_argument("--asset", default="SOL", help="Asset symbol to query.")
    parser.add_argument("--question", default="Why is SOL moving?", help="Question to send.")
    parser.add_argument("--lookback-minutes", type=int, default=60, help="Lookback window in minutes.")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds.")
    args = parser.parse_args()

    summary: dict[str, Any] = {
        "gateway_health": {"status": "error"},
        "orchestrator_health": {"status": "error"},
        "explain": {"status": "error"},
        "chat": {"status": "error"},
    }

    try:
        gateway_health = _request_json(f"{args.gateway_url.rstrip('/')}/healthz", timeout=args.timeout)
        summary["gateway_health"] = {
            "status": _status_label(bool(gateway_health.get("ok"))),
            "openai_enabled": gateway_health.get("openai_enabled"),
        }
    except Exception as exc:
        summary["gateway_health"] = {"status": "error", "message": f"{type(exc).__name__}: {exc}"}

    try:
        orchestrator_health = _request_json(f"{args.orchestrator_url.rstrip('/')}/healthz", timeout=args.timeout)
        summary["orchestrator_health"] = {
            "status": _status_label(bool(orchestrator_health.get("ok"))),
            "openai_enabled": orchestrator_health.get("openai_enabled"),
            "no_trading": orchestrator_health.get("no_trading"),
        }
    except Exception as exc:
        summary["orchestrator_health"] = {"status": "error", "message": f"{type(exc).__name__}: {exc}"}

    explain_payload = {
        "asset": args.asset,
        "question": args.question,
        "lookback_minutes": args.lookback_minutes,
    }
    try:
        explain = _request_json(
            f"{args.orchestrator_url.rstrip('/')}/v1/explain",
            method="POST",
            payload=explain_payload,
            timeout=args.timeout,
        )
        summary["explain"] = {
            "status": "ok",
            "provider": (explain.get("assistant_status") or {}).get("provider"),
            "fallback": (explain.get("assistant_status") or {}).get("fallback"),
            "confidence": explain.get("confidence") or explain.get("confidence_score"),
            "execution_disabled": explain.get("execution_disabled"),
            "current_cause": explain.get("current_cause"),
        }
    except Exception as exc:
        summary["explain"] = {"status": "error", "message": f"{type(exc).__name__}: {exc}"}

    try:
        chat = _request_json(
            f"{args.gateway_url.rstrip('/')}/v1/chat",
            method="POST",
            payload=explain_payload,
            timeout=args.timeout,
        )
        summary["chat"] = {
            "status": "ok",
            "provider": (chat.get("chat_status") or {}).get("provider"),
            "fallback": (chat.get("chat_status") or {}).get("fallback"),
            "assistant_response": chat.get("assistant_response"),
        }
    except Exception as exc:
        summary["chat"] = {"status": "error", "message": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(summary, indent=2))

    critical_keys = ("gateway_health", "orchestrator_health", "explain", "chat")
    return 0 if all(summary[key]["status"] == "ok" for key in critical_keys) else 1


if __name__ == "__main__":
    raise SystemExit(main())
