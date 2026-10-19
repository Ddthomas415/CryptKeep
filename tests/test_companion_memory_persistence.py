"""Opt-in disposable PostgreSQL and on-disk Qdrant-local contract proof.

Run with CBP_TEST_MEMORY_PERSISTENCE=1 in a temporary dependency environment.
No external database DSN is accepted; PostgreSQL listens only on a temp socket.
"""
import asyncio
import os
import shutil
import subprocess
from types import SimpleNamespace

import pytest

from tests.test_companion_memory_recovery import document, harness, ingest
from tests.test_companion_restored_routes import modules


def cleanup_owned_cluster(client, pg_ctl, data):
    try:
        if client is not None:
            client.close()
    finally:
        status = subprocess.run([pg_ctl, "-D", str(data), "status"],
                                capture_output=True, timeout=30)
        if status.returncode == 0:
            subprocess.run([pg_ctl, "-D", str(data), "-m", "fast", "-w", "stop"],
                           check=True, capture_output=True, timeout=30)
        elif status.returncode != 3:
            raise RuntimeError(f"owned_cluster_status_unknown:{status.returncode}")


def test_cleanup_stops_cluster_after_unsuccessful_start(monkeypatch):
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, "run", run)
    cleanup_owned_cluster(None, "pg_ctl", "/fixture/owned")
    assert calls[-1][-1] == "stop"


def test_cleanup_stops_cluster_even_if_index_close_fails(monkeypatch):
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0)
    def close():
        raise RuntimeError("close failed")
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(RuntimeError, match="close failed"):
        cleanup_owned_cluster(SimpleNamespace(close=close), "pg_ctl", "/fixture/owned")
    assert calls[-1][-1] == "stop"


def test_cleanup_does_not_stop_absent_cluster(monkeypatch):
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=3)
    monkeypatch.setattr(subprocess, "run", run)
    cleanup_owned_cluster(None, "pg_ctl", "/fixture/owned")
    assert len(calls) == 1 and calls[0][-1] == "status"


@pytest.mark.skipif(os.environ.get("CBP_TEST_MEMORY_PERSISTENCE") != "1",
                    reason="explicit disposable integration opt-in required")
@pytest.mark.parametrize("pipeline", [False, True, "imported"])
def test_persisted_row_reindexed_and_retrieved_after_reopen(tmp_path, pipeline, request, monkeypatch):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    qdrant = pytest.importorskip("qdrant_client")
    from qdrant_client.http import models as qm

    initdb, pg_ctl = shutil.which("initdb"), shutil.which("pg_ctl")
    if not initdb or not pg_ctl:
        pytest.skip("local PostgreSQL binaries required")
    data, socket = tmp_path / "pg", tmp_path / "socket"
    socket.mkdir()
    subprocess.run([initdb, "-D", str(data), "-A", "trust", "-U", "proof"],
                   check=True, capture_output=True, timeout=30)
    client = None
    try:
        subprocess.run([pg_ctl, "-D", str(data), "-l", str(tmp_path / "pg.log"),
                        "-o", f"-k {socket} -h ''", "-w", "start"],
                       check=True, capture_output=True, timeout=30)
        def query(sql, params=(), many=False):
            with psycopg.connect(host=str(socket), user="proof", dbname="postgres",
                                 autocommit=True, row_factory=dict_row) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    if cursor.description:
                        return cursor.fetchall() if many else cursor.fetchone()

        query("""CREATE TABLE documents (
            id BIGSERIAL PRIMARY KEY, source_type TEXT NOT NULL,
            source TEXT NOT NULL, url TEXT NOT NULL, title TEXT NOT NULL,
            content_text TEXT NOT NULL, timeline_tag TEXT NOT NULL,
            asset_tags TEXT[] NOT NULL, confidence DOUBLE PRECISION NOT NULL,
            content_hash TEXT NOT NULL UNIQUE, published_at TIMESTAMPTZ,
            fetched_at TIMESTAMPTZ NOT NULL, raw_object_key TEXT, metadata JSONB)""")
        query("""CREATE TABLE market_ticks (event_ts TIMESTAMPTZ, symbol TEXT,
            source TEXT, price DOUBLE PRECISION, bid DOUBLE PRECISION,
            ask DOUBLE PRECISION, volume DOUBLE PRECISION, raw_payload JSONB)""")
        client = qdrant.QdrantClient(path=str(tmp_path / "vectors"))
        client.create_collection("fixture", vectors_config=qm.VectorParams(
            size=64, distance=qm.Distance.COSINE))
        h = harness([])
        if pipeline == "imported":
            loaded = request.getfixturevalue("modules")
            memory = loaded["memory_retrieval"]
            h.ns = vars(memory)
            memory.settings.qdrant_collection = "fixture"
            async def no_audit(*args, **kwargs):
                pass
            monkeypatch.setattr(memory, "emit_audit_event", no_audit)
        h.ns.update(db=SimpleNamespace(fetch_one=query,
                    fetch_all=lambda sql, params: query(sql, params, many=True)), qm=qm)
        def fail(**kwargs):
            raise RuntimeError("injected index outage")
        h.ns["_qdrant_client"] = lambda: SimpleNamespace(upsert=fail)
        if pipeline:
            from tests.companion_pipeline_support import parsed_fixture, http_boundary
            candidate = parsed_fixture()
            if pipeline == "imported":
                import httpx
                parser = loaded["parser_normalizer"]
                monkeypatch.setattr(parser, "emit_audit_event", no_audit)
                async def parse():
                    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=parser.app),
                                                 base_url="http://disposable") as client:
                        return await client.post("/v1/parse/html", headers={"Authorization": "Bearer fixture-token"},
                            json={"url": candidate.url, "source": candidate.source, "source_type": "news",
                                  "html": "<title>Original</title><p>Bitcoin was volatile.</p>",
                                  "metadata": {"updated_at": "2026-01-02T00:00:00Z"}})
                parsed = asyncio.run(parse())
                parsed.raise_for_status()
                from shared.models import NormalizedDocument
                candidate = NormalizedDocument(**parsed.json()["document"])
                candidate.raw_html = None
                async def request(path, payload, token="Bearer fixture-token"):
                    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=memory.app),
                                                 base_url="http://disposable") as client:
                        return await client.post(path, json=payload, headers={"Authorization": token})
            else:
                request = http_boundary(h)
            assert asyncio.run(request("/v1/memory/documents",
                candidate.model_dump(mode="json"), "Bearer wrong")).status_code == 401
            assert query("SELECT count(*) AS n FROM documents")["n"] == 0
            def write(doc):
                response = asyncio.run(request("/v1/memory/documents", doc.model_dump(mode="json")))
                response.raise_for_status()
                return SimpleNamespace(**response.json())
        else:
            candidate = document(metadata={"updated_at": "2026-01-02T00:00:00Z"})
            write = lambda doc: ingest(h, doc)
        with pytest.raises(RuntimeError, match="injected index outage"):
            write(candidate)
        assert query("SELECT count(*) AS n FROM documents")["n"] == 1
        h.ns["_qdrant_client"] = lambda: client
        req = SimpleNamespace(asset="BTC", lookback_minutes=60, limit=5, question="Original")
        def retrieve():
            if pipeline:
                response = asyncio.run(request("/v1/memory/retrieve", vars(req)))
                response.raise_for_status()
                return response.json()
            return asyncio.run(h.ns["retrieve_context"](req, "Bearer fixture-token"))
        assert retrieve()["vector_matches"] == []
        retry = candidate.model_copy(update={"title": "Changed retry", "asset_tags": ["ETH"]}) if pipeline else document(title="Changed retry", asset_tags=["ETH"])
        result = write(retry)
        assert result.ok and result.duplicate
        client.close()
        client = qdrant.QdrantClient(path=str(tmp_path / "vectors"))
        matches = retrieve()["vector_matches"]
        assert len(matches) == 1 and matches[0]["id"] == result.document_id
        assert matches[0]["title"] == "Original" and matches[0]["published_at"] is None
        if pipeline:
            assert matches[0]["source"] == "example.org"
            assert matches[0]["url"] == candidate.url
            row = query("SELECT content_hash, content_text, asset_tags FROM documents")
            assert row["content_hash"] == candidate.content_hash
            assert row["content_text"] == candidate.content_text
            assert row["asset_tags"] == ["BTC"]
            if pipeline == "imported":
                evidence = loaded["orchestrator"]._build_evidence({"get_signal_summary": retrieve()})
                cited = next(item for item in evidence if item.get("document_id") == result.document_id)
                assert cited["url"] == candidate.url
                assert cited["summary"] == "Original"
        assert query("SELECT metadata FROM documents")["metadata"] == {
            "updated_at": "2026-01-02T00:00:00Z"}
        req.asset = "ETH"
        assert retrieve()["vector_matches"] == []
    finally:
        cleanup_owned_cluster(client, pg_ctl, data)
