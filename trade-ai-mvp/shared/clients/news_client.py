from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None


async def fetch_newsapi_articles(asset: str, api_key: str, timeout: float = 10.0) -> list[dict[str, Any]]:
    if not api_key or httpx is None:
        return []

    params = {
        "q": asset,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": api_key,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get("https://newsapi.org/v2/everything", params=params)
            resp.raise_for_status()
            payload = resp.json()
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    for item in payload.get("articles", [])[:5]:
        out.append(
            {
                "external_id": item.get("url"),
                "url": item.get("url"),
                "title": item.get("title") or f"{asset} update",
                "author": item.get("author"),
                "published_at": item.get("publishedAt") or datetime.now(timezone.utc).isoformat(),
                "raw_text": item.get("content") or item.get("description") or "",
                "timeline": "present",
            }
        )
    return out
