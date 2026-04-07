from __future__ import annotations

import os
from typing import Any

from services.ai_copilot.policy import DEFAULT_MODEL, DEFAULT_PROVIDER, MAX_TOKENS


def call_llm(*, system: str, user: str) -> dict[str, Any]:
    provider = os.environ.get("CBP_COPILOT_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    model = os.environ.get("CBP_COPILOT_MODEL", DEFAULT_MODEL).strip()

    if provider == "anthropic":
        try:
            import anthropic
        except Exception as exc:
            return {"ok": False, "error": f"Anthropic SDK not available: {type(exc).__name__}: {exc}"}
        api_key = os.environ.get("CBP_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"ok": False, "error": "Missing Anthropic API key"}
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = msg.content[0].text if msg.content else ""
        return {"ok": True, "text": text, "provider": provider, "model": model}

    if provider == "openai":
        try:
            from openai import OpenAI
        except Exception as exc:
            return {"ok": False, "error": f"OpenAI SDK not available: {type(exc).__name__}: {exc}"}
        api_key = os.environ.get("CBP_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {"ok": False, "error": "Missing OpenAI API key"}
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
        return {"ok": True, "text": text, "provider": provider, "model": model}

    if provider == "google":
        try:
            from google import genai
        except Exception as exc:
            return {"ok": False, "error": f"Google GenAI SDK not available: {type(exc).__name__}: {exc}"}
        api_key = os.environ.get("CBP_GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return {"ok": False, "error": "Missing Google API key"}
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model,
            contents=f"{system}\n\n{user}",
        )
        text = getattr(resp, "text", "") or ""
        return {"ok": True, "text": text, "provider": provider, "model": model}

    return {"ok": False, "error": f"Unsupported provider: {provider}"}
