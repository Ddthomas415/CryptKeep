from __future__ import annotations

import re
from typing import Any

from qdrant_client import QdrantClient
from sqlalchemy import and_, cast, desc, select, String

from shared.config import Settings
from shared.models.documents import Document


def _keyword_score(text: str, query: str) -> float:
    if not text or not query:
        return 0.0
    terms = [t for t in re.split(r"\W+", query.lower()) if t]
    if not terms:
        return 0.0
    low = text.lower()
    hits = sum(1 for t in terms if t in low)
    return hits / max(1, len(terms))


def _vector_bonus(query: str, docs: list[Document], settings: Settings) -> dict[str, float]:
    # Wiring only: graceful fallback if qdrant unavailable or collection empty.
    try:
        client = QdrantClient(url=settings.qdrant_url, timeout=2.0)
        _ = client.get_collections()
    except Exception:
        return {str(d.id): 0.0 for d in docs}

    # No embedding model in Phase 1 scaffold, return neutral scores.
    return {str(d.id): 0.0 for d in docs}


def search_documents(db, settings: Settings, query: str, asset: str, timeline: list[str], limit: int) -> list[dict[str, Any]]:
    asset = asset.upper()
    timeline = timeline or ["past", "present", "future"]

    rows = db.execute(
        select(Document)
        .where(
            and_(
                Document.timeline.in_(timeline),
                cast(Document.metadata_json["asset_tags"], String).ilike(f"%{asset}%"),
            )
        )
        .order_by(desc(Document.published_at), desc(Document.ingested_at))
        .limit(max(20, limit * 4))
    ).scalars().all()

    bonus = _vector_bonus(query, rows, settings)

    scored: list[tuple[float, Document]] = []
    for d in rows:
        text = f"{d.title or ''} {d.cleaned_text or ''}"
        kw = _keyword_score(text, query)
        conf = float(d.confidence or 0.5)
        score = (kw * 0.55) + (conf * 0.35) + (bonus.get(str(d.id), 0.0) * 0.10)
        scored.append((score, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, d in scored[:limit]:
        out.append(
            {
                "id": str(d.id),
                "source": "newsapi_or_seed",
                "title": d.title or "",
                "url": d.url,
                "timeline": d.timeline,
                "confidence": float(d.confidence or 0.5),
                "published_at": d.published_at.isoformat() if d.published_at else None,
                "snippet": (d.cleaned_text or "")[:240],
                "score": round(float(score), 4),
            }
        )
    return out
