"""Exercise recovered functions without importing or starting historical services."""
import ast
import asyncio
import hashlib
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

import pytest


def recovered():
    path = Path(__file__).resolve().parents[1] / "research/companion_recovery/news_ingestion.py"
    tree = ast.parse(path.read_text())
    functions = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name in {"_published_at", "_service_headers", "_fingerprint", "_poll_once",
                                "_parse_via_service", "_store_document"}]
    ns = dict(asyncio=asyncio, hashlib=hashlib, datetime=datetime, timezone=timezone,
              urlparse=urlparse, Any=object, parsedate_to_datetime=parsedate_to_datetime)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), "exec"), ns)
    return ns


@pytest.mark.parametrize("value", ["Tue, 29 Sep 2026 08:00:00 -0400",
                                   "2026-09-29T12:00:00Z"])
def test_publication_contract(value):
    import importlib.util
    path = Path(__file__).resolve().parents[1] / "research/companion_recovery/models.py"
    spec = importlib.util.spec_from_file_location("recovery_models", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.NormalizedDocument.model_rebuild(_types_namespace=vars(module))
    timestamp = recovered()["_published_at"](value)
    doc = module.NormalizedDocument(source="fixture", url="https://example.org",
        title="BTC event", content_text="Fixture only", content_hash="fixture",
        published_at=timestamp, fetched_at="2026-09-29T12:01:00Z")
    assert doc.published_at.isoformat() == "2026-09-29T12:00:00+00:00"


@pytest.mark.parametrize("value", ["bad date", "2026-09-29T12:00:00"])
def test_invalid_publication_is_not_invented(value):
    with pytest.raises(ValueError):
        recovered()["_published_at"](value)


def test_absent_publication_stays_unknown():
    assert recovered()["_published_at"](None) is None


def test_missing_auth_fails_before_network():
    ns = recovered()
    ns["settings"] = SimpleNamespace(service_token="")
    for fn, args in [("_store_document", ({},)), ("_parse_via_service", ())]:
        kwargs = {} if args else dict(url="https://example.org", source="test",
                                     source_type="news", published_at=None)
        with pytest.raises(RuntimeError, match="service_auth_not_configured"):
            asyncio.run(ns[fn](*args, **kwargs))


def test_both_service_calls_forward_auth():
    ns = recovered()
    calls = []
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, endpoint, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"ok": True})
    async def retry(call, **kwargs): return await call()
    ns.update(httpx=SimpleNamespace(AsyncClient=Client), retry_async=retry,
              settings=SimpleNamespace(service_token="test-only", parser_service_url="http://parser",
                                       memory_service_url="http://memory", request_timeout_seconds=1))
    asyncio.run(ns["_parse_via_service"](url="https://example.org", source="test",
                                        source_type="news", published_at=None))
    asyncio.run(ns["_store_document"]({"source": "test"}))
    assert len(calls) == 2
    assert all(c["headers"] == {"Authorization": "Bearer test-only"} for c in calls)


@pytest.mark.parametrize("failure", ["exception", "unconfirmed"])
def test_failed_storage_remains_retryable(failure):
    ns = recovered()
    attempts = []
    doc = {"source": "example.org", "published_at": "2026-09-29T00:00:00Z"}
    async def parse(**kwargs): return {"document": doc}
    async def store(document):
        attempts.append(document)
        if len(attempts) == 1:
            if failure == "exception": raise RuntimeError("unavailable")
            return {"ok": False}
        return {"ok": True}
    async def audit(*args, **kwargs): pass
    ns.update(settings=SimpleNamespace(news_rss_list=["https://example.org/rss"]),
              feedparser=SimpleNamespace(parse=lambda url: SimpleNamespace(entries=[
                  {"link": "https://example.org/article", "title": "Event"}])),
              state=SimpleNamespace(errors=0, polls=0, ingested=0, skipped=0), _seen=set(),
              _parse_via_service=parse, _store_document=store, emit_audit_event=audit,
              logger=SimpleNamespace(error=lambda *args, **kwargs: None))
    assert asyncio.run(ns["_poll_once"]())["poll_ingested"] == 0
    assert not ns["_seen"]
    assert asyncio.run(ns["_poll_once"]())["poll_ingested"] == 1
    assert asyncio.run(ns["_poll_once"]())["poll_skipped"] == 1
    assert attempts == [doc, doc]


def poll_payload_harness(entry, text, *, fail_store_once=False):
    """Unit boundary harness: real recovered bodies, fake extraction and I/O."""
    ns = recovered()
    path = Path(__file__).resolve().parents[1] / "research/companion_recovery/parser_normalizer.py"
    tree = ast.parse(path.read_text())
    names = {"_infer_timeline", "_extract_assets", "_confidence", "_hash_content", "_build_doc"}
    constants = {"ASSET_PATTERNS", "FUTURE_HINTS", "PAST_HINTS"}
    nodes = [n for n in tree.body if
             (isinstance(n, ast.FunctionDef) and n.name in names)
             or (isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                 and n.target.id in constants)
             or (isinstance(n, ast.Assign) and any(
                 isinstance(t, ast.Name) and t.id in constants for t in n.targets))]
    parser = dict(Any=object, re=re, hashlib=hashlib, datetime=datetime, timezone=timezone,
                  _extract_text_and_title=lambda html: (text, "Fixture"))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), parser)
    calls = []
    audits = []

    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, endpoint, *, json, headers):
            calls.append((endpoint, json))
            if endpoint.endswith("/v1/parse/url"):
                # Emulate request defaults, not HTTP validation or HTML extraction.
                result = {"document": parser["_build_doc"](
                    **json, html="fixture", timeline_hint=json.get("timeline_hint"))}
            else:
                if fail_store_once and sum(url.endswith("/v1/memory/documents")
                                           for url, _ in calls) == 1:
                    raise RuntimeError("storage unavailable")
                result = {"ok": True}
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: result)

    async def retry(call, **kwargs): return await call()
    async def audit(*args, **kwargs): audits.append((args, kwargs))
    ns.update(httpx=SimpleNamespace(AsyncClient=Client), retry_async=retry,
              settings=SimpleNamespace(service_token="test-only", parser_service_url="http://parser",
                  memory_service_url="http://memory", request_timeout_seconds=1,
                  news_rss_list=["https://example.org/rss"]),
              feedparser=SimpleNamespace(parse=lambda url: SimpleNamespace(entries=[entry])),
              state=SimpleNamespace(errors=0, polls=0, ingested=0, skipped=0), _seen=set(),
              emit_audit_event=audit, logger=SimpleNamespace(error=lambda *args, **kwargs: None))
    return ns, calls, audits


@pytest.mark.parametrize("text,expected", [("Bitcoin was volatile", "past"),
                                           ("Bitcoin will change", "future")])
@pytest.mark.parametrize("dates,published,updated", [
    ({}, None, None),
    ({"updated": "Tue, 29 Sep 2026 08:00:00 -0400"}, None, "2026-09-29T12:00:00+00:00"),
    ({"published": "2026-09-28T08:00:00-04:00", "updated": "2026-09-29T12:00:00Z"},
     "2026-09-28T12:00:00+00:00", "2026-09-29T12:00:00+00:00"),
])
def test_poll_parser_store_preserves_inference_and_dates(text, expected, dates, published, updated):
    ns, calls, _ = poll_payload_harness(
        {"link": "https://example.org/article", "title": "Fixture", **dates}, text)
    assert asyncio.run(ns["_poll_once"]())["poll_ingested"] == 1
    assert [url for url, _ in calls] == ["http://parser/v1/parse/url", "http://memory/v1/memory/documents"]
    request, stored = [payload for _, payload in calls]
    assert "timeline_hint" not in request
    assert stored["timeline_tag"] == expected
    for payload in (request, stored):
        assert payload["published_at"] == published
        assert payload["metadata"] == {"ingested_by": "news-ingestion", "updated_at": updated}


@pytest.mark.parametrize("field", ["published", "updated"])
@pytest.mark.parametrize("value", ["bad date", "2026-09-29T12:00:00"])
def test_poll_invalid_dates_remain_retryable(field, value):
    entry = {"link": "https://example.org/article", field: value}
    ns, calls, audits = poll_payload_harness(entry, "Bitcoin was volatile")
    for _ in range(2):
        assert asyncio.run(ns["_poll_once"]())["poll_ingested"] == 0
        assert not ns["_seen"]
    assert calls == []
    assert ns["state"].errors == 2
    assert sum(args[1] == "news_ingest_entry_failed" for args, _ in audits) == 2
    entry[field] = "2026-09-29T12:00:00Z"
    assert asyncio.run(ns["_poll_once"]())["poll_ingested"] == 1
    assert len(calls) == 2


def test_poll_payload_survives_storage_failure_and_repoll():
    ns, calls, _ = poll_payload_harness(
        {"link": "https://example.org/article", "updated": "2026-09-29T12:00:00Z"},
        "Bitcoin will change", fail_store_once=True)
    assert asyncio.run(ns["_poll_once"]())["poll_ingested"] == 0
    assert not ns["_seen"]
    assert asyncio.run(ns["_poll_once"]())["poll_ingested"] == 1
    assert asyncio.run(ns["_poll_once"]())["poll_skipped"] == 1
    assert len(calls) == 4
    assert calls[0] == calls[2]
    for _, stored in calls[1::2]:
        assert stored["published_at"] is None
        assert stored["metadata"]["updated_at"] == "2026-09-29T12:00:00+00:00"
        assert stored["timeline_tag"] == "future"
