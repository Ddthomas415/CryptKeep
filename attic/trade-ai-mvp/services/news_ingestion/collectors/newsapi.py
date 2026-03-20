from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shared.clients.news_client import fetch_newsapi_articles


def sample_articles(asset: str) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    return [
        {
            "external_id": f"sample-{asset}-1",
            "url": f"https://example.com/{asset.lower()}-momentum",
            "title": f"{asset} gains as network activity rises",
            "author": "Research Desk",
            "published_at": now.isoformat(),
            "raw_text": f"{asset} shows present momentum with increased spot volume and market participation.",
            "timeline": "present",
        },
        {
            "external_id": f"sample-{asset}-2",
            "url": f"https://example.com/{asset.lower()}-liquidity",
            "title": f"Liquidity deepens for {asset} pairs",
            "author": "Exchange Watch",
            "published_at": now.isoformat(),
            "raw_text": f"Current order books for {asset} show tighter spreads and higher depth.",
            "timeline": "present",
        },
    ]


async def fetch_articles(asset: str, api_key: str) -> list[dict[str, Any]]:
    live = await fetch_newsapi_articles(asset, api_key)
    if live:
        return live
    return sample_articles(asset)
