from __future__ import annotations

import asyncio
import hashlib
import hmac
from contextlib import suppress
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import feedparser
import httpx
from fastapi import FastAPI, Header, HTTPException

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.logging import configure_logging
from shared.retry import retry_async

# Recovered from ad18488df^; isolated candidate, not wired into startup.
settings = get_settings()
logger = configure_logging(settings.service_name or "news-ingestion", settings.log_level)

def _require_service_token(authorization: str | None) -> None:
    expected = str(getattr(settings, "service_token", "") or "")
    if not expected:
        raise HTTPException(status_code=503, detail="service_auth_not_configured")
    supplied = str(authorization or "").strip()
    prefix = "Bearer "
    if not supplied.startswith(prefix):
        raise HTTPException(status_code=401, detail="unauthorized")
    token = supplied[len(prefix):].strip()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="unauthorized")

app = FastAPI(title="news-ingestion", version="0.1.0")

_stop = asyncio.Event()
_task: asyncio.Task | None = None


class NewsState:
    polls: int = 0
    ingested: int = 0
    skipped: int = 0
    errors: int = 0
    last_poll: str | None = None


state = NewsState()
_seen: set[str] = set()


def _fingerprint(link: str, title: str) -> str:
    h = hashlib.sha256()
    h.update((link or "").encode("utf-8", errors="ignore"))
    h.update(b"\n")
    h.update((title or "").encode("utf-8", errors="ignore"))
    return h.hexdigest()


def _service_headers() -> dict[str, str]:
    token = str(getattr(settings, "service_token", "") or "").strip()
    if not token:
        raise RuntimeError("service_auth_not_configured")
    return {"Authorization": f"Bearer {token}"}


def _published_at(value: str | None) -> str | None:
    if not value:
        return None
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        date = parsedate_to_datetime(value)
    if date.tzinfo is None or date.utcoffset() is None:
        raise ValueError("publication_timezone_required")
    return date.astimezone(timezone.utc).isoformat()


async def _parse_via_service(
    *,
    url: str,
    source: str,
    source_type: str,
    published_at: str | None,
    updated_at: str | None = None,
) -> dict[str, Any]:
    headers = _service_headers()

    async def _call() -> dict[str, Any]:
        payload = {
            "url": url,
            "source": source,
            "source_type": source_type,
            "asset_hint": [],
            "published_at": published_at,
            "metadata": {"ingested_by": "news-ingestion", "updated_at": updated_at},
        }
        endpoint = f"{settings.parser_service_url.rstrip('/')}/v1/parse/url"
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            res = await client.post(endpoint, json=payload, headers=headers)
            res.raise_for_status()
            return res.json()

    return await retry_async(_call, retries=3, base_delay=0.5)


async def _store_document(doc: dict[str, Any]) -> dict[str, Any]:
    headers = _service_headers()

    async def _call() -> dict[str, Any]:
        endpoint = f"{settings.memory_service_url.rstrip('/')}/v1/memory/documents"
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            res = await client.post(endpoint, json=doc, headers=headers)
            res.raise_for_status()
            return res.json()

    return await retry_async(_call, retries=3, base_delay=0.5)


async def _poll_once() -> dict[str, Any]:
    poll_ingested = 0
    poll_skipped = 0

    for feed_url in settings.news_rss_list:
        parsed = await asyncio.to_thread(feedparser.parse, feed_url)
        entries = list(getattr(parsed, "entries", []) or [])

        for entry in entries:
            link = str(entry.get("link") or "").strip()
            title = str(entry.get("title") or "").strip()
            if not link:
                continue

            fp = _fingerprint(link, title)
            if fp in _seen:
                poll_skipped += 1
                continue

            source = urlparse(feed_url).netloc or "rss"

            try:
                parsed_doc = await _parse_via_service(
                    url=link,
                    source=source,
                    source_type="news",
                    published_at=_published_at(entry.get("published")),
                    # FeedParserDict.get aliases absent updated to published.
                    updated_at=_published_at(dict(entry).get("updated")),
                )
                document = parsed_doc.get("document") if isinstance(parsed_doc, dict) else None
                if not isinstance(document, dict):
                    raise RuntimeError("parser_no_document")
                stored = await _store_document(document)
                if not isinstance(stored, dict) or stored.get("ok") is not True:
                    raise RuntimeError("storage_not_confirmed")
                _seen.add(fp)
                poll_ingested += 1
            except Exception as exc:
                state.errors += 1
                logger.error(
                    "news_ingest_entry_failed",
                    extra={"context": {"feed_url": feed_url, "url": link, "error_type": type(exc).__name__}},
                )
                await emit_audit_event(
                    "news-ingestion",
                    "news_ingest_entry_failed",
                    status="error",
                    payload={"feed_url": feed_url, "url": link, "error_type": type(exc).__name__},
                )

    state.polls += 1
    state.ingested += poll_ingested
    state.skipped += poll_skipped
    state.last_poll = datetime.now(timezone.utc).isoformat()

    payload = {
        "feeds": settings.news_rss_list,
        "poll_ingested": poll_ingested,
        "poll_skipped": poll_skipped,
        "total_ingested": state.ingested,
    }
    await emit_audit_event("news-ingestion", "poll_complete", payload=payload)
    return {"ok": True, **payload}


async def _poll_loop() -> None:
    while not _stop.is_set():
        try:
            await _poll_once()
        except Exception as exc:
            state.errors += 1
            logger.error("news_poll_failed", extra={"context": {"error_type": type(exc).__name__}})
            await emit_audit_event(
                "news-ingestion",
                "poll_failed",
                status="error",
                payload={"error_type": type(exc).__name__},
            )
        await asyncio.sleep(max(30.0, settings.news_poll_seconds))


@app.on_event("startup")
async def startup() -> None:
    global _task
    _stop.clear()
    _task = asyncio.create_task(_poll_loop())


@app.on_event("shutdown")
async def shutdown() -> None:
    _stop.set()
    if _task is not None:
        _task.cancel()
        with suppress(asyncio.CancelledError):
            await _task


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "service": "news-ingestion",
        "ok": True,
        "last_poll": state.last_poll,
        "polls": state.polls,
        "ingested": state.ingested,
        "skipped": state.skipped,
        "errors": state.errors,
        "feeds": settings.news_rss_list,
    }


@app.post("/v1/news/poll-now")
async def poll_now(authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
    _require_service_token(authorization)
    return await _poll_once()
