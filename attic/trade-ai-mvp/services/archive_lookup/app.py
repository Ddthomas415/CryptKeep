from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI
from sqlalchemy import and_, cast, select, String

from services.archive_lookup.providers.wayback import fetch_archive_context
from shared.audit_client import emit_audit_event
from shared.config import get_settings
from shared.db import SessionLocal, check_db_connection
from shared.logging import get_logger
from shared.models.documents import Document

settings = get_settings("archive_lookup")
logger = get_logger("archive_lookup", settings.log_level)
app = FastAPI(title="archive_lookup")


@app.on_event("startup")
def startup() -> None:
    ok = check_db_connection()
    logger.info("startup_db_check", extra={"context": {"ok": ok}})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/archive/{asset}")
async def archive(asset: str) -> dict[str, Any]:
    asset = asset.upper()
    live = await fetch_archive_context(asset, settings.wayback_base_url)

    with SessionLocal() as db:
        docs = db.execute(
            select(Document)
            .where(
                and_(
                    Document.timeline == "past",
                    cast(Document.metadata_json["asset_tags"], String).ilike(f"%{asset}%"),
                )
            )
            .order_by(Document.published_at.desc().nullslast())
            .limit(3)
        ).scalars().all()

    seeded = [
        {
            "title": d.title,
            "url": d.url,
            "timeline": d.timeline,
            "timestamp": d.published_at.isoformat() if d.published_at else None,
            "source": "seeded_archive",
        }
        for d in docs
    ]

    items = seeded or live
    if not items:
        items = [
            {
                "title": f"Historical context unavailable for {asset}",
                "url": None,
                "timeline": "past",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "source": "fallback",
            }
        ]

    await emit_audit_event(
        settings=settings,
        service_name="archive_lookup",
        event_type="archive_lookup",
        message="Archive context fetched",
        payload={"asset": asset, "count": len(items)},
    )
    return {"asset": asset, "items": items}
