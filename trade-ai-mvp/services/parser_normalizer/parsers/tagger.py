from __future__ import annotations

import hashlib
import re
from datetime import datetime

ASSET_SYMBOLS = ("BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA")


def infer_timeline_tag(text: str, published_at: datetime | None = None) -> str:
    low = (text or "").lower()

    future_terms = ("will", "upcoming", "scheduled", "roadmap", "proposal", "unlock", "launch")
    past_terms = ("last year", "previous", "historical", "earlier", "was", "were")

    if any(term in low for term in past_terms):
        return "past"
    if any(term in low for term in future_terms):
        return "future"

    if published_at:
        now = datetime.utcnow().timestamp()
        if published_at.timestamp() < now - (86400 * 30):
            return "past"

    return "present"


def extract_asset_tags(text: str) -> list[str]:
    found: set[str] = set()
    for asset in ASSET_SYMBOLS:
        if re.search(rf"\b{asset}\b", text or "", flags=re.IGNORECASE):
            found.add(asset)
    return sorted(found)


def compute_content_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update((part or "").encode("utf-8", errors="ignore"))
        h.update(b"\n")
    return h.hexdigest()
