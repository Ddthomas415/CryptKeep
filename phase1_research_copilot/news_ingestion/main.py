from __future__ import annotations

import asyncio
import hashlib
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import feedparser
import httpx
from fastapi import FastAPI

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.logging import configure_logging
from shared.retry import retry_async

settings = get_settings()
logger = configure_logging(settings.service_name or "news-ingestion", settings.log_level)

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


async def _parse_via_service(
    *,
    url: str,
    source: str,
    source_type: str,
    published_at: str | None,
) -> dict[str, Any]:
    async def _call() -> dict[str, Any]:
        payload = {
            "url": url,
            "source": source,
            "source_type": source_type,
            "timeline_hint": "present",
            "asset_hint": [],
            "published_at": published_at,
            "metadata": {"ingested_by": "news-ingestion"},
        }
        endpoint = f"{settings.parser_service_url.rstrip('/')}/v1/parse/url"
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            res = await client.post(endpoint, json=payload)
            res.raise_for_status()
            return res.json()

    return await retry_async(_call, retries=3, base_delay=0.5)


async def _store_document(doc: dict[str, Any]) -> dict[str, Any]:
    async def _call() -> dict[str, Any]:
        endpoint = f"{settings.memory_service_url.rstrip('/')}/v1/memory/documents"
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            res = await client.post(endpoint, json=doc)
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

            _seen.add(fp)
            source = urlparse(feed_url).netloc or "rss"
            published = entry.get("published") or entry.get("updated")

            try:
                parsed_doc = await _parse_via_service(
                    url=link,
                    source=source,
                    source_type="news",
                    published_at=published,
                )
                document = parsed_doc.get("document") if isinstance(parsed_doc, dict) else None
                if not isinstance(document, dict):
                    raise RuntimeError("parser_no_document")
                await _store_document(document)
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
async def poll_now() -> dict[str, Any]:
    return await _poll_once()
