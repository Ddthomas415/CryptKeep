"""Real recovered function bodies with in-memory SQL/vector boundaries only."""
import ast
import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from types import SimpleNamespace

import pytest


class UpdateStatus(str, Enum):
    COMPLETED = "completed"
    ACKNOWLEDGED = "acknowledged"


class AuthError(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail


def harness(outcomes):
    path = Path(__file__).resolve().parents[1] / "research/companion_recovery/memory_retrieval.py"
    tree = ast.parse(path.read_text())
    names = {"_require_service_token", "_embed", "_index_document", "ingest_document",
             "retrieve_context", "_normalize_asset", "_compute_market_summary"}
    nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
             and n.name in names]
    for node in nodes:
        node.decorator_list = []
    rows, calls, audits, sql_calls, raw_calls = {}, [], [], [], []
    indexed = {}

    def fetch_one(sql, params):
        sql_calls.append((sql, params))
        if sql.startswith("SELECT"):
            assert "content_text" in sql and "fetched_at" in sql
            return rows.get(params[0])
        assert "RETURNING id, title, content_text" in sql
        fields = ("source_type", "source", "url", "title", "content_text", "timeline_tag",
                  "asset_tags", "confidence", "content_hash", "published_at", "fetched_at",
                  "raw_object_key", "metadata")
        row = dict(zip(fields, params), id=73)
        rows[row["content_hash"]] = row
        return row

    def fetch_all(sql, params):
        sql_calls.append((sql, params))
        if "WHERE id = ANY" in sql:
            return [row for row in rows.values() if row["id"] in params[0]]
        return []

    def upsert(**kwargs):
        calls.append(kwargs)
        assert kwargs["wait"] is True
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if getattr(outcome, "status", None) == UpdateStatus.COMPLETED:
            for point in kwargs["points"]:
                indexed[point.id] = point
        return outcome

    async def audit(*args, **kwargs):
        audits.append((args, kwargs))

    def search(**kwargs):
        assets = kwargs["query_filter"].must[0].match.any
        return [SimpleNamespace(id=point.id) for point in indexed.values()
                if set(assets).intersection(point.payload["asset_tags"])][:kwargs["limit"]]

    client = SimpleNamespace(upsert=upsert, search=search)
    ns = dict(Any=object, hashlib=hashlib, hmac=hmac, json=json, datetime=datetime,
              timezone=timezone, EMBED_DIM=64, NormalizedDocument=object, RetrieveRequest=object,
              IngestResponse=SimpleNamespace, Header=lambda **kwargs: None, HTTPException=AuthError,
              settings=SimpleNamespace(service_token="fixture-token", qdrant_collection="fixture"),
              db=SimpleNamespace(fetch_one=fetch_one, fetch_all=fetch_all),
              qm=SimpleNamespace(PointStruct=SimpleNamespace, UpdateStatus=UpdateStatus,
                  Filter=SimpleNamespace, FieldCondition=SimpleNamespace, MatchAny=SimpleNamespace),
              _qdrant_client=lambda: client,
              _store_raw_html=lambda *args: raw_calls.append(args), emit_audit_event=audit,
              logger=SimpleNamespace(info=lambda *args, **kwargs: None))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), ns)
    return SimpleNamespace(ns=ns, rows=rows, calls=calls, audits=audits,
                           sql_calls=sql_calls, raw_calls=raw_calls, indexed=indexed)


def document(**changes):
    values = dict(source_type="news", source="original", url="https://example.org/original",
                  title="Original", content_text="Persisted text", timeline_tag="past",
                  asset_tags=["BTC"], confidence=0.8, content_hash="same-hash",
                  published_at=None, fetched_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                  raw_html=None, metadata={})
    return SimpleNamespace(**(values | changes))


def ingest(h, doc=None, token="Bearer fixture-token"):
    return asyncio.run(h.ns["ingest_document"](doc or document(), token))


def completed():
    return SimpleNamespace(status=UpdateStatus.COMPLETED)


def test_failed_index_retry_reindexes_persisted_row():
    h = harness([RuntimeError("index unavailable"), completed()])
    with pytest.raises(RuntimeError, match="index unavailable"):
        ingest(h)
    assert len(h.rows) == 1 and not h.audits
    result = ingest(h)
    assert result.ok is True and result.duplicate is True and result.document_id == 73
    assert len(h.raw_calls) == 1
    assert len(h.calls) == 2
    assert vars(h.calls[0]["points"][0]) == vars(h.calls[1]["points"][0])
    assert [a[0][1] for a in h.audits] == ["ingest_document_duplicate"]


def test_repeated_index_failure_never_reports_success():
    h = harness([RuntimeError("offline"), RuntimeError("offline")])
    for _ in range(2):
        with pytest.raises(RuntimeError, match="offline"):
            ingest(h)
    assert len(h.rows) == 1 and len(h.calls) == 2 and not h.audits


def test_changed_duplicate_cannot_poison_vector_or_payload():
    h = harness([RuntimeError("offline"), completed()])
    with pytest.raises(RuntimeError):
        ingest(h)
    changed = document(title="Poison", content_text="Changed", source_type="other",
                       source="changed", url="https://example.org/changed", timeline_tag="future",
                       asset_tags=["ETH"], confidence=0.1, fetched_at="changed", raw_html="changed")
    assert ingest(h, changed).duplicate is True
    point = h.calls[1]["points"][0]
    assert vars(point) == vars(h.calls[0]["points"][0])
    assert point.vector == h.ns["_embed"]("Original\nPersisted text")
    assert point.payload["source"] == "original" and point.id == 73
    assert len(h.raw_calls) == 1


@pytest.mark.parametrize("status", [None, "acknowledged", "unknown"])
def test_uncompleted_acknowledgement_rejected_on_insert_and_duplicate(status):
    response = None if status is None else SimpleNamespace(status=status)
    h = harness([response, response, completed()])
    for _ in range(2):
        with pytest.raises(RuntimeError, match="vector_upsert_not_completed"):
            ingest(h)
    assert not h.audits
    assert ingest(h).ok is True


def test_completed_insert_acknowledgement():
    h = harness([completed()])
    result = ingest(h)
    assert result.ok is True and result.duplicate is False and result.document_id == 73
    assert h.calls[0]["wait"] is True
    assert h.audits[0][0][1] == "ingest_document"


@pytest.mark.parametrize("configured,token,status", [
    ("", "Bearer fixture-token", 503), ("fixture-token", None, 401),
    ("fixture-token", "Bearer wrong", 401), ("fixture-token", "fixture-token", 401),
])
@pytest.mark.parametrize("endpoint", ["ingest_document", "retrieve_context"])
def test_auth_failure_has_no_io(configured, token, status, endpoint):
    h = harness([])
    h.ns["settings"].service_token = configured
    with pytest.raises(AuthError) as error:
        asyncio.run(h.ns[endpoint](document(), token))
    assert error.value.status_code == status
    assert not h.sql_calls and not h.calls and not h.raw_calls and not h.audits


def test_retrieval_uses_vector_ids_to_load_stored_documents():
    h = harness([completed()])
    ingest(h)
    req = SimpleNamespace(asset="btc/usd", lookback_minutes=60, limit=5, question="Original?")
    result = asyncio.run(h.ns["retrieve_context"](req, "Bearer fixture-token"))
    assert result["ok"] is True and result["asset"] == "BTC"
    assert result["vector_matches"] == [h.rows["same-hash"]]
    assert h.sql_calls[-1][1] == ([73],)


@pytest.mark.parametrize("failure", [RuntimeError("offline"),
                                     SimpleNamespace(status=UpdateStatus.ACKNOWLEDGED)])
def test_retrieval_visibility_requires_completed_retry(failure):
    h = harness([failure, completed()])
    req = SimpleNamespace(asset="BTC", lookback_minutes=60, limit=5, question="Original?")
    with pytest.raises(RuntimeError):
        ingest(h)
    assert len(h.rows) == 1 and not h.indexed
    before = asyncio.run(h.ns["retrieve_context"](req, "Bearer fixture-token"))
    assert before["vector_matches"] == []
    ingest(h, document(title="Changed retry", asset_tags=["ETH"]))
    after = asyncio.run(h.ns["retrieve_context"](req, "Bearer fixture-token"))
    assert after["vector_matches"] == [h.rows["same-hash"]]
    assert after["vector_matches"][0]["title"] == "Original"
    assert list(h.indexed) == [73]
    req.asset = "ETH"
    unrelated = asyncio.run(h.ns["retrieve_context"](req, "Bearer fixture-token"))
    assert unrelated["vector_matches"] == []
