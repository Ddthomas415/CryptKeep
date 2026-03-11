from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from services.parser_normalizer.parsers.html_parser import clean_html_to_text
from services.parser_normalizer.parsers.tagger import (
    compute_content_hash,
    extract_asset_tags,
    infer_timeline_tag,
)
from shared.audit_client import emit_audit_event
from shared.config import get_settings
from shared.logging import get_logger

settings = get_settings("parser_normalizer")
logger = get_logger("parser_normalizer", settings.log_level)
app = FastAPI(title="parser_normalizer")


class NormalizeRequest(BaseModel):
    title: str | None = None
    url: str | None = None
    raw_text: str | None = None
    html: str | None = None
    published_at: datetime | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/normalize")
async def normalize(req: NormalizeRequest) -> dict[str, Any]:
    text = req.raw_text or ""
    if req.html:
        text = clean_html_to_text(req.html)
    timeline = infer_timeline_tag(text, req.published_at)
    assets = extract_asset_tags(f"{req.title or ''} {text}")
    content_hash = compute_content_hash(req.title or "", req.url or "", text)

    payload = {
        "title": req.title,
        "url": req.url,
        "raw_text": req.raw_text,
        "cleaned_text": text,
        "timeline": timeline,
        "asset_tags": assets,
        "content_hash": content_hash,
    }
    logger.info("normalized_document", extra={"context": {"timeline": timeline, "asset_tags": assets}})
    await emit_audit_event(
        settings=settings,
        service_name="parser_normalizer",
        event_type="normalize",
        message="Document normalized",
        payload={"timeline": timeline, "asset_tags": assets, "url": req.url},
    )
    return payload
