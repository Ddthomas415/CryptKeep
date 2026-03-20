from __future__ import annotations

from typing import Any

from shared.clients.archive_client import lookup_wayback


async def fetch_archive_context(asset: str, base_url: str) -> list[dict[str, Any]]:
    return await lookup_wayback(asset, base_url)
