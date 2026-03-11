from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.logging import configure_logging
from shared.retry import retry_async

settings = get_settings()
logger = configure_logging(settings.service_name or "parser-normalizer", settings.log_level)

app = FastAPI(title="parser-normalizer", version="0.1.0")

ASSET_PATTERNS: dict[str, tuple[str, ...]] = {
    "BTC": ("BTC", "Bitcoin"),
    "ETH": ("ETH", "Ethereum"),
    "SOL": ("SOL", "Solana"),
    "BNB": ("BNB", "Binance Coin"),
    "XRP": ("XRP", "Ripple"),
}

FUTURE_HINTS = (
    "will",
    "upcoming",
    "next",
    "roadmap",
    "scheduled",
    "launch",
    "proposal",
    "vote",
    "unlock",
)
PAST_HINTS = (
    "last year",
    "previous",
    "historical",
    "earlier",
    "was",
    "were",
    "in 20",
)


class ParseUrlRequest(BaseModel):
    url: str
    source: str
    source_type: str = "news"
    timeline_hint: str | None = None
    asset_hint: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParseHtmlRequest(BaseModel):
    url: str
    source: str
    html: str
    source_type: str = "archive"
    timeline_hint: str | None = None
    asset_hint: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def _extract_text_and_title(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.string if soup.title and soup.title.string else "").strip()
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text, title


def _infer_timeline(text: str, timeline_hint: str | None) -> str:
    if timeline_hint in {"past", "present", "future"}:
        return str(timeline_hint)
    low = text.lower()
    if any(k in low for k in FUTURE_HINTS):
        return "future"
    if any(k in low for k in PAST_HINTS):
        return "past"
    return "present"


def _extract_assets(text: str, asset_hint: list[str]) -> list[str]:
    found = {a.upper() for a in asset_hint if str(a).strip()}
    for symbol, patterns in ASSET_PATTERNS.items():
        for pattern in patterns:
            if re.search(rf"\b{re.escape(pattern)}\b", text, flags=re.IGNORECASE):
                found.add(symbol)
                break
    return sorted(found)


def _confidence(text: str, timeline: str) -> float:
    base = 0.45
    if len(text) > 600:
        base += 0.2
    elif len(text) > 200:
        base += 0.1
    if timeline in {"past", "future"}:
        base += 0.1
    return min(0.95, round(base, 3))


def _hash_content(url: str, title: str, text: str) -> str:
    h = hashlib.sha256()
    h.update(url.encode("utf-8", errors="ignore"))
    h.update(b"\n")
    h.update(title.encode("utf-8", errors="ignore"))
    h.update(b"\n")
    h.update(text.encode("utf-8", errors="ignore"))
    return h.hexdigest()


async def _fetch_url(url: str) -> str:
    async def _call() -> str:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True) as client:
            res = await client.get(url)
            res.raise_for_status()
            return res.text

    return await retry_async(_call, retries=3, base_delay=0.6)


def _build_doc(
    *,
    url: str,
    source: str,
    source_type: str,
    html: str,
    timeline_hint: str | None,
    asset_hint: list[str],
    published_at: datetime | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    text, title = _extract_text_and_title(html)
    timeline = _infer_timeline(text, timeline_hint)
    assets = _extract_assets(f"{title} {text}", asset_hint)
    content_hash = _hash_content(url, title, text)
    fetched_at = datetime.now(timezone.utc)

    return {
        "source_type": source_type,
        "source": source,
        "url": url,
        "title": title or url,
        "content_text": text,
        "timeline_tag": timeline,
        "asset_tags": assets,
        "confidence": _confidence(text, timeline),
        "content_hash": content_hash,
        "published_at": published_at,
        "fetched_at": fetched_at.isoformat(),
        "raw_html": html,
        "metadata": metadata,
    }


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"service": "parser-normalizer", "ok": True}


@app.post("/v1/parse/url")
async def parse_url(req: ParseUrlRequest) -> dict[str, Any]:
    html = await _fetch_url(req.url)
    doc = _build_doc(
        url=req.url,
        source=req.source,
        source_type=req.source_type,
        html=html,
        timeline_hint=req.timeline_hint,
        asset_hint=req.asset_hint,
        published_at=req.published_at,
        metadata=req.metadata,
    )
    await emit_audit_event(
        "parser-normalizer",
        "parse_url",
        payload={
            "url": req.url,
            "content_hash": doc["content_hash"],
            "timeline_tag": doc["timeline_tag"],
            "asset_tags": doc["asset_tags"],
        },
    )
    logger.info("parse_url_ok", extra={"context": {"url": req.url, "hash": doc["content_hash"]}})
    return {"ok": True, "document": doc}


@app.post("/v1/parse/html")
async def parse_html(req: ParseHtmlRequest) -> dict[str, Any]:
    doc = _build_doc(
        url=req.url,
        source=req.source,
        source_type=req.source_type,
        html=req.html,
        timeline_hint=req.timeline_hint,
        asset_hint=req.asset_hint,
        published_at=req.published_at,
        metadata=req.metadata,
    )
    await emit_audit_event(
        "parser-normalizer",
        "parse_html",
        payload={
            "url": req.url,
            "content_hash": doc["content_hash"],
            "timeline_tag": doc["timeline_tag"],
            "asset_tags": doc["asset_tags"],
        },
    )
    return {"ok": True, "document": doc}
