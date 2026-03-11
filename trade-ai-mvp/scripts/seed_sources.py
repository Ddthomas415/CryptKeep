from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from services.parser_normalizer.parsers.tagger import compute_content_hash
from shared.db import SessionLocal
from shared.models.documents import Document, Source
from shared.models.events import Event
from shared.models.market import MarketSnapshot

SEED_SOURCES = [
    {"name": "coinbase", "source_type": "exchange", "base_url": "https://api.exchange.coinbase.com"},
    {"name": "newsapi", "source_type": "news", "base_url": "https://newsapi.org"},
    {"name": "wayback", "source_type": "archive", "base_url": "https://archive.org"},
]


def _source_id(db, name: str):
    row = db.execute(select(Source).where(Source.name == name)).scalar_one_or_none()
    return row.id if row else None


def main() -> None:
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        added_sources = 0
        for src in SEED_SOURCES:
            exists = db.execute(select(Source).where(Source.name == src["name"])).scalar_one_or_none()
            if exists:
                continue
            db.add(
                Source(
                    name=src["name"],
                    source_type=src["source_type"],
                    base_url=src["base_url"],
                    trust_score=Decimal("0.80") if src["name"] == "coinbase" else Decimal("0.60"),
                    is_enabled=True,
                )
            )
            added_sources += 1
        db.commit()

        # Seed SOL market snapshot
        existing_snap = db.execute(
            select(MarketSnapshot).where(MarketSnapshot.symbol == "SOL-USD").order_by(MarketSnapshot.ts.desc()).limit(1)
        ).scalar_one_or_none()
        if not existing_snap:
            db.add(
                MarketSnapshot(
                    exchange="coinbase",
                    symbol="SOL-USD",
                    last_price=Decimal("145.20"),
                    bid=Decimal("145.10"),
                    ask=Decimal("145.30"),
                    spread=Decimal("0.20"),
                    raw={"seeded": True},
                )
            )

        news_source_id = _source_id(db, "newsapi")
        wayback_source_id = _source_id(db, "wayback")

        docs = [
            {
                "source_id": news_source_id,
                "title": "SOL rises as active addresses climb",
                "url": "https://example.com/sol-active-addresses",
                "timeline": "present",
                "text": "SOL is moving as on-chain active addresses and volume increase in the current session.",
                "published_at": now - timedelta(minutes=45),
                "confidence": Decimal("0.8200"),
                "metadata": {"asset_tags": ["SOL"], "seeded": True},
            },
            {
                "source_id": news_source_id,
                "title": "Derivatives open interest expands for SOL",
                "url": "https://example.com/sol-open-interest",
                "timeline": "present",
                "text": "Current derivatives participation in SOL has expanded with higher open interest.",
                "published_at": now - timedelta(minutes=20),
                "confidence": Decimal("0.7800"),
                "metadata": {"asset_tags": ["SOL"], "seeded": True},
            },
            {
                "source_id": wayback_source_id,
                "title": "Historical Solana roadmap milestone precedent",
                "url": "https://archive.org/details/solana-roadmap-2024",
                "timeline": "past",
                "text": "Past roadmap announcements for SOL were followed by similar market expansions.",
                "published_at": now - timedelta(days=365),
                "confidence": Decimal("0.7400"),
                "metadata": {"asset_tags": ["SOL"], "seeded": True},
            },
            {
                "source_id": news_source_id,
                "title": "Upcoming SOL governance vote scheduled next week",
                "url": "https://example.com/sol-governance-vote",
                "timeline": "future",
                "text": "A governance proposal for SOL will be voted on next week and may affect liquidity.",
                "published_at": now + timedelta(days=7),
                "confidence": Decimal("0.7600"),
                "metadata": {"asset_tags": ["SOL"], "seeded": True},
            },
        ]

        inserted_docs = 0
        for d in docs:
            content_hash = compute_content_hash(d["title"], d["url"], d["text"])
            exists = db.execute(select(Document).where(Document.content_hash == content_hash)).scalar_one_or_none()
            if exists:
                continue
            db.add(
                Document(
                    source_id=d["source_id"],
                    external_id=d["url"],
                    url=d["url"],
                    title=d["title"],
                    author="seed",
                    published_at=d["published_at"],
                    timeline=d["timeline"],
                    content_type="article",
                    language="en",
                    raw_text=d["text"],
                    cleaned_text=d["text"],
                    summary=d["title"],
                    content_hash=content_hash,
                    confidence=d["confidence"],
                    metadata_json=d["metadata"],
                )
            )
            inserted_docs += 1

        existing_event = db.execute(
            select(Event).where(Event.asset_symbol == "SOL", Event.event_type == "governance")
        ).scalar_one_or_none()
        if not existing_event:
            db.add(
                Event(
                    asset_symbol="SOL",
                    event_type="governance",
                    timeline="future",
                    event_time=now + timedelta(days=7),
                    confidence=Decimal("0.7000"),
                    headline="SOL governance vote",
                    details={"seeded": True, "note": "future catalyst"},
                )
            )

        db.commit()

    print(
        {
            "status": "ok",
            "sources_seeded": len(SEED_SOURCES),
            "docs_inserted": inserted_docs,
            "flow_ready_for": "Why is SOL moving?",
        }
    )


if __name__ == "__main__":
    main()
