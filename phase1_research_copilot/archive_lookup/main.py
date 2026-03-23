from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.logging import configure_logging
from shared.retry import retry_async

settings = get_settings()
logger = configure_logging(settings.service_name or "archive-lookup", settings.log_level)

app = FastAPI(title="archive-lookup", version="0.1.0")


class ArchiveLookupRequest(BaseModel):
    url: str
    asset: str
    max_snapshots: int = 3
    ingest: bool = True


async def _cdx_lookup(url: str, max_snapshots: int) -> list[dict[str, str]]:
    async def _call() -> list[dict[str, str]]:
        endpoint = "https://web.archive.org/cdx/search/cdx"
        params = {
            "url": url,
            "output": "json",
            "fl": "timestamp,original,statuscode,mimetype",
            "filter": "statuscode:200",
            "limit": str(max_snapshots),
            "from": "2017",
        }
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            resp = await client.get(endpoint, params=params)
            resp.raise_for_status()
            rows = resp.json()
            if not isinstance(rows, list) or len(rows) <= 1:
                return []
            out: list[dict[str, str]] = []
            for row in rows[1:]:
                if not isinstance(row, list) or len(row) < 4:
                    continue
                out.append(
                    {
                        "timestamp": str(row[0]),
                        "original": str(row[1]),
                        "statuscode": str(row[2]),
                        "mimetype": str(row[3]),
                    }
                )
            return out

    return await retry_async(_call, retries=3, base_delay=0.8)


async def _fetch_archive_html(timestamp: str, original: str) -> str:
    async def _call() -> str:
        archive_url = f"https://web.archive.org/web/{timestamp}/{original}"
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True) as client:
            resp = await client.get(archive_url)
            resp.raise_for_status()
            return resp.text

    return await retry_async(_call, retries=3, base_delay=0.8)


async def _parse_html(url: str, html: str, asset: str) -> dict[str, Any]:
    endpoint = f"{settings.parser_service_url.rstrip('/')}/v1/parse/html"
    payload = {
        "url": url,
        "source": "wayback",
        "source_type": "archive",
        "html": html,
        "timeline_hint": "past",
        "asset_hint": [asset],
        "published_at": None,
        "metadata": {"provider": "wayback"},
    }
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(endpoint, json=payload)
        resp.raise_for_status()
        return resp.json()


async def _ingest_document(doc: dict[str, Any]) -> dict[str, Any]:
    endpoint = f"{settings.memory_service_url.rstrip('/')}/v1/memory/documents"
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(endpoint, json=doc)
        resp.raise_for_status()
        return resp.json()


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"service": "archive-lookup", "ok": True}


@app.post("/v1/archive/lookup")
async def lookup(req: ArchiveLookupRequest) -> dict[str, Any]:
    snapshots = await _cdx_lookup(req.url, max(1, min(req.max_snapshots, 10)))
    docs: list[dict[str, Any]] = []

    for snap in snapshots:
        original = snap["original"]
        timestamp = snap["timestamp"]
        archive_url = f"https://web.archive.org/web/{timestamp}/{original}"
        try:
            html = await _fetch_archive_html(timestamp, original)
            parsed = await _parse_html(archive_url, html, req.asset)
            doc = parsed.get("document") if isinstance(parsed, dict) else None
            if not isinstance(doc, dict):
                continue
            if req.ingest:
                await _ingest_document(doc)
            docs.append(
                {
                    "timestamp": timestamp,
                    "archive_url": archive_url,
                    "title": doc.get("title"),
                    "timeline_tag": doc.get("timeline_tag"),
                    "asset_tags": doc.get("asset_tags"),
                    "confidence": doc.get("confidence"),
                }
            )
        except Exception as exc:
            logger.error(
                "archive_snapshot_failed",
                extra={"context": {"archive_url": archive_url, "error_type": type(exc).__name__}},
            )
            await emit_audit_event(
                "archive-lookup",
                "archive_snapshot_failed",
                status="error",
                payload={"archive_url": archive_url, "error_type": type(exc).__name__},
            )

    payload = {
        "url": req.url,
        "asset": req.asset,
        "snapshot_count": len(snapshots),
        "document_count": len(docs),
        "ingest": req.ingest,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    await emit_audit_event("archive-lookup", "archive_lookup", payload=payload)
    return {"ok": True, **payload, "documents": docs}
