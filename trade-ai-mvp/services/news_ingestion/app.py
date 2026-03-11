from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import FastAPI
from sqlalchemy import and_, cast, select, String

from services.news_ingestion.collectors.newsapi import fetch_articles
from services.parser_normalizer.parsers.tagger import compute_content_hash, extract_asset_tags, infer_timeline_tag
from shared.audit_client import emit_audit_event
from shared.config import get_settings
from shared.db import SessionLocal, check_db_connection
from shared.logging import get_logger
from shared.models.documents import Document, Source

settings = get_settings("news_ingestion")
logger = get_logger("news_ingestion", settings.log_level)
app = FastAPI(title="news_ingestion")


@app.on_event("startup")
def startup() -> None:
    ok = check_db_connection()
    logger.info("startup_db_check", extra={"context": {"ok": ok}})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _source_id(db, name: str) -> Any:
    src = db.execute(select(Source).where(Source.name == name)).scalar_one_or_none()
    return src.id if src else None


def _store_documents(asset: str, docs: list[dict[str, Any]]) -> int:
    inserted = 0
    with SessionLocal() as db:
        source_id = _source_id(db, "newsapi")
        for item in docs:
            raw_text = str(item.get("raw_text") or "")
            title = str(item.get("title") or "")
            clean = raw_text.strip()
            timeline = item.get("timeline") or infer_timeline_tag(f"{title} {clean}")
            content_hash = compute_content_hash(title, item.get("url") or "", clean)
            exists = db.execute(select(Document).where(Document.content_hash == content_hash)).scalar_one_or_none()
            if exists:
                continue

            tags = extract_asset_tags(f"{title} {clean}")
            if asset.upper() not in tags:
                tags.append(asset.upper())

            doc = Document(
                source_id=source_id,
                external_id=item.get("external_id"),
                url=item.get("url"),
                title=title,
                author=item.get("author"),
                published_at=_to_dt(item.get("published_at")),
                timeline=timeline,
                content_type="article",
                language="en",
                raw_text=raw_text,
                cleaned_text=clean,
                summary=title,
                content_hash=content_hash,
                confidence=Decimal("0.7000"),
                metadata_json={"asset_tags": tags, "provider": "newsapi_or_seed"},
            )
            db.add(doc)
            inserted += 1
        db.commit()
    return inserted


def _to_dt(v: Any) -> datetime | None:
    if isinstance(v, datetime):
        return v
    if isinstance(v, str) and v:
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)
    return None


@app.post("/ingest/news")
async def ingest_news(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    asset = str((payload or {}).get("asset") or "SOL").upper()
    docs = await fetch_articles(asset, settings.newsapi_api_key)
    inserted = _store_documents(asset, docs)
    logger.info("news_ingested", extra={"context": {"asset": asset, "inserted": inserted}})
    await emit_audit_event(
        settings=settings,
        service_name="news_ingestion",
        event_type="news_ingested",
        message="News ingestion completed",
        payload={"asset": asset, "inserted": inserted},
    )
    return {"inserted": inserted, "asset": asset}


@app.get("/news/{asset}")
async def get_news(asset: str) -> dict[str, Any]:
    asset = asset.upper()
    with SessionLocal() as db:
        rows = db.execute(
            select(Document)
            .where(
                and_(
                    Document.timeline == "present",
                    cast(Document.metadata_json["asset_tags"], String).ilike(f"%{asset}%"),
                )
            )
            .order_by(Document.ingested_at.desc())
            .limit(5)
        ).scalars().all()

        items = [
            {
                "id": str(r.id),
                "title": r.title,
                "url": r.url,
                "timeline": r.timeline,
                "published_at": r.published_at.isoformat() if r.published_at else None,
                "confidence": float(r.confidence or 0),
                "source": "newsapi",
            }
            for r in rows
        ]

    await emit_audit_event(
        settings=settings,
        service_name="news_ingestion",
        event_type="news_query",
        message="News queried",
        payload={"asset": asset, "count": len(items)},
    )
    return {"asset": asset, "items": items}
