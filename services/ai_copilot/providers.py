from __future__ import annotations

import logging
import os
from typing import Any

from services.audit.operator_event_journal import append_operator_event
from services.ai_copilot.policy import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    EXTERNAL_PROVIDER_ALLOWLIST_ENV,
    MAX_TOKENS,
    external_provider_policy,
)

_LOG = logging.getLogger(__name__)


def _with_operator_event(
    *,
    provider: str,
    model: str,
    system: str,
    user: str,
    outcome: dict[str, Any],
) -> dict[str, Any]:
    result = "success" if bool(outcome.get("ok")) else "failed"
    error = str(outcome.get("error") or "")
    try:
        event = append_operator_event(
            actor="system",
            action="ai_copilot_external_provider_call",
            target=str(provider or "unknown"),
            result=result,
            reason="call_llm",
            pre_state={
                "provider": provider,
                "model": model,
                "system_prompt_chars": len(str(system or "")),
                "user_prompt_chars": len(str(user or "")),
            },
            post_state={
                "ok": bool(outcome.get("ok")),
                "provider": outcome.get("provider") or provider,
                "model": outcome.get("model") or model,
                "error_present": bool(error),
                "error_type": error.split(":", 1)[0] if error else "",
            },
            source="services.ai_copilot.providers",
            extra={"prompt_payload_logged": False},
        )
        return {
            **outcome,
            "operator_event": {
                "ok": True,
                "event_id": event.get("event_id"),
                "path": event.get("path"),
            },
        }
    except Exception as exc:
        _LOG.warning(
            "AI copilot provider operator event journal failed: %s: %s",
            type(exc).__name__,
            exc,
        )
        return {
            **outcome,
            "operator_event": {
                "ok": False,
                "reason": f"operator_event_write_failed:{type(exc).__name__}",
            },
        }


def call_llm(*, system: str, user: str) -> dict[str, Any]:
    provider = os.environ.get("CBP_COPILOT_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    model = os.environ.get("CBP_COPILOT_MODEL", DEFAULT_MODEL).strip()
    provider_policy = external_provider_policy(
        provider,
        allowlist_raw=os.environ.get(EXTERNAL_PROVIDER_ALLOWLIST_ENV),
    )
    if not bool(provider_policy.get("ok")):
        return _with_operator_event(
            provider=provider,
            model=model,
            system=system,
            user=user,
            outcome={
                "ok": False,
                "error": str(provider_policy.get("reason") or "provider_policy_blocked"),
                "provider": provider,
                "model": model,
                "provider_policy": provider_policy,
            },
        )

    if provider == "anthropic":
        try:
            import anthropic
        except Exception as exc:
            return _with_operator_event(
                provider=provider,
                model=model,
                system=system,
                user=user,
                outcome={
                    "ok": False,
                    "error": f"Anthropic SDK not available: {type(exc).__name__}: {exc}",
                },
            )
        api_key = os.environ.get("CBP_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return _with_operator_event(
                provider=provider,
                model=model,
                system=system,
                user=user,
                outcome={"ok": False, "error": "Missing Anthropic API key"},
            )
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = msg.content[0].text if msg.content else ""
        return _with_operator_event(
            provider=provider,
            model=model,
            system=system,
            user=user,
            outcome={"ok": True, "text": text, "provider": provider, "model": model},
        )

    if provider == "openai":
        try:
            from openai import OpenAI
        except Exception as exc:
            return _with_operator_event(
                provider=provider,
                model=model,
                system=system,
                user=user,
                outcome={
                    "ok": False,
                    "error": f"OpenAI SDK not available: {type(exc).__name__}: {exc}",
                },
            )
        api_key = os.environ.get("CBP_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return _with_operator_event(
                provider=provider,
                model=model,
                system=system,
                user=user,
                outcome={"ok": False, "error": "Missing OpenAI API key"},
            )
        client = OpenAI(api_key=api_key)
        resp = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_output_tokens=MAX_TOKENS,
        )
        text = getattr(resp, "output_text", "") or ""
        return _with_operator_event(
            provider=provider,
            model=model,
            system=system,
            user=user,
            outcome={"ok": True, "text": text, "provider": provider, "model": model},
        )

    if provider == "google":
        try:
            from google import genai
        except Exception as exc:
            return _with_operator_event(
                provider=provider,
                model=model,
                system=system,
                user=user,
                outcome={
                    "ok": False,
                    "error": f"Google GenAI SDK not available: {type(exc).__name__}: {exc}",
                },
            )
        api_key = os.environ.get("CBP_GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return _with_operator_event(
                provider=provider,
                model=model,
                system=system,
                user=user,
                outcome={"ok": False, "error": "Missing Google API key"},
            )
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model,
            contents=f"{system}\n\n{user}",
        )
        text = getattr(resp, "text", "") or ""
        return _with_operator_event(
            provider=provider,
            model=model,
            system=system,
            user=user,
            outcome={"ok": True, "text": text, "provider": provider, "model": model},
        )

    return _with_operator_event(
        provider=provider,
        model=model,
        system=system,
        user=user,
        outcome={"ok": False, "error": f"Unsupported provider: {provider}"},
    )
