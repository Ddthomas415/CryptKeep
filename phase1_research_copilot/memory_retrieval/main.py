from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.config import Config as BotoConfig
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.db import Database
from shared.logging import configure_logging
from shared.models import NormalizedDocument, RetrieveRequest

settings = get_settings()
logger = configure_logging(settings.service_name or "memory-retrieval", settings.log_level)
db = Database(settings.database_url)

EMBED_DIM = 64

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


class IngestResponse(BaseModel):
    ok: bool
    document_id: int
    duplicate: bool = False


app = FastAPI(title="memory-retrieval", version="0.1.0")

_qdrant: QdrantClient | None = None
_s3 = None


def _qdrant_client() -> QdrantClient:
    global _qdrant
    if _qdrant is None:
        _qdrant = QdrantClient(url=settings.qdrant_url)
    return _qdrant


def _s3_client():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            endpoint_url=settings.minio_endpoint,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=BotoConfig(s3={"addressing_style": "path"}),
            region_name="us-east-1",
        )
    return _s3


def _ensure_bucket() -> None:
    s3 = _s3_client()
    buckets = s3.list_buckets().get("Buckets", [])
    names = {b.get("Name") for b in buckets}
    if settings.minio_bucket not in names:
        s3.create_bucket(Bucket=settings.minio_bucket)


def _ensure_qdrant_collection() -> None:
    client = _qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in existing:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qm.VectorParams(size=EMBED_DIM, distance=qm.Distance.COSINE),
        )


def _embed(text: str) -> list[float]:
    # Deterministic lightweight embedding stub; replace with model embeddings in Phase 2.
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).digest()
    vec: list[float] = []
    for i in range(EMBED_DIM):
        b = digest[i % len(digest)]
        vec.append(((b / 255.0) * 2.0) - 1.0)
    return vec


def _store_raw_html(content_hash: str, raw_html: str | None) -> str | None:
    if not raw_html:
        return None
    key = f"raw/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{content_hash}.html"
    _s3_client().put_object(
        Bucket=settings.minio_bucket,
        Key=key,
        Body=raw_html.encode("utf-8", errors="ignore"),
        ContentType="text/html",
    )
    return key


def _normalize_asset(asset: str) -> str:
    out = str(asset or "").upper().strip()
    return out.split("/")[0] if "/" in out else out


def _compute_market_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "ok": False,
            "reason": "no_market_data",
            "latest_price": None,
            "change_pct": 0.0,
            "window_samples": 0,
        }
    latest = rows[0]
    oldest = rows[-1]
    latest_price = float(latest.get("price") or 0.0)
    oldest_price = float(oldest.get("price") or latest_price or 1.0)
    change_pct = ((latest_price - oldest_price) / oldest_price * 100.0) if oldest_price else 0.0
    return {
        "ok": True,
        "latest_price": latest_price,
        "change_pct": round(change_pct, 4),
        "window_samples": len(rows),
        "latest_ts": latest.get("event_ts"),
        "latest_source": latest.get("source"),
    }


@app.on_event("startup")
def _startup() -> None:
    _ensure_bucket()
    _ensure_qdrant_collection()


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    db_ok = db.health().get("ok", False)
    q_ok = True
    s3_ok = True
    try:
        _qdrant_client().get_collections()
    except Exception:
        q_ok = False
    try:
        _s3_client().list_buckets()
    except Exception:
        s3_ok = False
    return {"service": "memory-retrieval", "ok": bool(db_ok and q_ok and s3_ok), "db": db_ok, "qdrant": q_ok, "minio": s3_ok}


@app.post("/v1/memory/documents", response_model=IngestResponse)
async def ingest_document(doc: NormalizedDocument, authorization: str | None = Header(default=None, alias="Authorization")) -> IngestResponse:
    _require_service_token(authorization)
    existing = db.fetch_one("SELECT id FROM documents WHERE content_hash = %s", (doc.content_hash,))
    if existing:
        doc_id = int(existing["id"])
        await emit_audit_event(
            "memory-retrieval",
            "ingest_document_duplicate",
            payload={"document_id": doc_id, "content_hash": doc.content_hash},
        )
        return IngestResponse(ok=True, document_id=doc_id, duplicate=True)

    raw_object_key = _store_raw_html(doc.content_hash, doc.raw_html)
    published_at = doc.published_at if doc.published_at else None
    fetched_at = doc.fetched_at if doc.fetched_at else datetime.now(timezone.utc)

    inserted = db.fetch_one(
        """
        INSERT INTO documents (
            source_type, source, url, title, content_text, timeline_tag,
            asset_tags, confidence, content_hash, published_at, fetched_at,
            raw_object_key, metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        RETURNING id
        """,
        (
            doc.source_type,
            doc.source,
            doc.url,
            doc.title,
            doc.content_text,
            doc.timeline_tag,
            doc.asset_tags,
            float(doc.confidence),
            doc.content_hash,
            published_at,
            fetched_at,
            raw_object_key,
            json.dumps(doc.metadata),
        ),
    )
    if not inserted:
        raise RuntimeError("insert_failed")

    doc_id = int(inserted["id"])
    vec = _embed(f"{doc.title}\n{doc.content_text}")
    _qdrant_client().upsert(
        collection_name=settings.qdrant_collection,
        points=[
            qm.PointStruct(
                id=doc_id,
                vector=vec,
                payload={
                    "document_id": doc_id,
                    "source_type": doc.source_type,
                    "timeline_tag": doc.timeline_tag,
                    "asset_tags": doc.asset_tags,
                    "url": doc.url,
                    "source": doc.source,
                    "confidence": float(doc.confidence),
                    "fetched_at": fetched_at.isoformat() if isinstance(fetched_at, datetime) else str(fetched_at),
                },
            )
        ],
    )

    await emit_audit_event(
        "memory-retrieval",
        "ingest_document",
        payload={"document_id": doc_id, "timeline_tag": doc.timeline_tag, "asset_tags": doc.asset_tags},
    )
    logger.info("document_ingested", extra={"context": {"document_id": doc_id, "hash": doc.content_hash}})
    return IngestResponse(ok=True, document_id=doc_id, duplicate=False)


@app.post("/v1/memory/retrieve")
async def retrieve_context(req: RetrieveRequest) -> dict[str, Any]:
    asset = _normalize_asset(req.asset)
    symbol_like = f"{asset}/%"

    market_rows = db.fetch_all(
        """
        SELECT event_ts, symbol, source, price, bid, ask, volume, raw_payload
        FROM market_ticks
        WHERE symbol ILIKE %s
          AND event_ts >= NOW() - (%s || ' minutes')::interval
        ORDER BY event_ts DESC
        LIMIT 240
        """,
        (symbol_like, int(req.lookback_minutes)),
    )
    market_summary = _compute_market_summary(market_rows)

    recent_news = db.fetch_all(
        """
        SELECT id, source_type, source, url, title, timeline_tag, asset_tags, confidence, published_at, fetched_at
        FROM documents
        WHERE %s = ANY(asset_tags)
          AND timeline_tag = 'present'
          AND fetched_at >= NOW() - (%s || ' minutes')::interval
        ORDER BY confidence DESC, fetched_at DESC
        LIMIT %s
        """,
        (asset, int(req.lookback_minutes), int(req.limit)),
    )

    past_context = db.fetch_all(
        """
        SELECT id, source_type, source, url, title, timeline_tag, asset_tags, confidence, published_at, fetched_at
        FROM documents
        WHERE %s = ANY(asset_tags)
          AND timeline_tag = 'past'
        ORDER BY confidence DESC, COALESCE(published_at, fetched_at) DESC
        LIMIT %s
        """,
        (asset, int(req.limit)),
    )

    future_context = db.fetch_all(
        """
        SELECT id, source_type, source, url, title, timeline_tag, asset_tags, confidence, published_at, fetched_at
        FROM documents
        WHERE %s = ANY(asset_tags)
          AND timeline_tag = 'future'
        ORDER BY confidence DESC, COALESCE(published_at, fetched_at) DESC
        LIMIT %s
        """,
        (asset, int(req.limit)),
    )

    vector_matches: list[dict[str, Any]] = []
    if req.question.strip():
        search_result = _qdrant_client().search(
            collection_name=settings.qdrant_collection,
            query_vector=_embed(req.question),
            query_filter=qm.Filter(
                must=[qm.FieldCondition(key="asset_tags", match=qm.MatchAny(any=[asset]))]
            ),
            limit=int(req.limit),
        )
        vector_ids = [int(p.id) for p in search_result]
        if vector_ids:
            in_params = tuple(vector_ids)
            sql = """
                SELECT id, source_type, source, url, title, timeline_tag, asset_tags, confidence, published_at, fetched_at
                FROM documents
                WHERE id = ANY(%s)
            """
            vector_matches = db.fetch_all(sql, (list(in_params),))

    payload = {
        "ok": True,
        "asset": asset,
        "question": req.question,
        "market": market_summary,
        "recent_news": recent_news,
        "past_context": past_context,
        "future_context": future_context,
        "vector_matches": vector_matches,
    }
    await emit_audit_event(
        "memory-retrieval",
        "retrieve_context",
        payload={
            "asset": asset,
            "lookback_minutes": req.lookback_minutes,
            "recent_news_count": len(recent_news),
            "past_count": len(past_context),
            "future_count": len(future_context),
            "vector_count": len(vector_matches),
        },
    )
    return payload
