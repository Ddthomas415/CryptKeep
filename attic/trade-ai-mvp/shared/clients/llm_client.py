from __future__ import annotations

from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None


async def polish_explanation(
    *,
    openai_api_key: str,
    model: str,
    draft: dict[str, Any],
    timeout: float = 12.0,
) -> dict[str, Any] | None:
    if not openai_api_key or httpx is None:
        return None

    system = (
        "You are a concise crypto research analyst. Improve wording while preserving factual content. "
        "Return JSON with keys: current_cause, past_precedent, future_catalyst."
    )
    user = {
        "question": draft.get("question"),
        "current_cause": draft.get("current_cause"),
        "past_precedent": draft.get("past_precedent"),
        "future_catalyst": draft.get("future_catalyst"),
    }

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "text", "text": system}]},
            {"role": "user", "content": [{"type": "text", "text": str(user)}]},
        ],
    }
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post("https://api.openai.com/v1/responses", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text_parts = []
            for output in data.get("output", []):
                for content in output.get("content", []):
                    if content.get("type") == "output_text":
                        text_parts.append(content.get("text", ""))
            if not text_parts:
                return None
            import json

            return json.loads(text_parts[-1])
    except Exception:
        return None
