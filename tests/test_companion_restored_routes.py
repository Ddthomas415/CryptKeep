"""Imported companion routes; ASGI only, no lifespan or background activation."""
import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture
def modules(monkeypatch):
    pytest.importorskip("pydantic_settings")
    pytest.importorskip("boto3")
    pytest.importorskip("feedparser")
    root = Path(__file__).parents[1] / "phase1_research_copilot"
    monkeypatch.syspath_prepend(str(root))
    from shared import config
    settings = config.Settings(_env_file=None, service_token="fixture-token")
    monkeypatch.setattr(config, "get_settings", lambda: settings)
    result = {}
    for name in ("parser_normalizer", "memory_retrieval", "news_ingestion", "gateway", "orchestrator", "archive_lookup"):
        spec = importlib.util.spec_from_file_location("proof_" + name, root / name / "main.py")
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, spec.name, module)
        spec.loader.exec_module(module)
        result[name] = module
    return result


def request(module, path, payload, token="Bearer fixture-token"):
    import httpx
    async def call():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=module.app),
                                     base_url="http://fixture") as client:
            return await client.post(path, json=payload, headers={"Authorization": token})
    return asyncio.run(call())


@pytest.mark.parametrize("name,path,payload", [
    ("parser_normalizer", "/v1/parse/html", {"url": "https://example.org", "source": "fixture", "html": "Bitcoin"}),
    ("memory_retrieval", "/v1/memory/retrieve", {"asset": "BTC", "question": "Why?"}),
    ("news_ingestion", "/v1/news/poll-now", {}),
    ("gateway", "/v1/chat", {"asset": "BTC", "question": "Why?"}),
    ("orchestrator", "/v1/explain", {"asset": "BTC", "question": "Why?"}),
    ("archive_lookup", "/v1/archive/lookup", {"asset": "BTC", "url": "https://example.org"}),
])
def test_actual_routes_deny_wrong_or_missing_configured_auth(modules, name, path, payload):
    module = modules[name]
    assert request(module, path, payload, "Bearer wrong").status_code == 401
    module.settings.service_token = ""
    assert request(module, path, payload).status_code == 503


@pytest.mark.parametrize("name", ["gateway", "orchestrator"])
def test_unresolved_header_cannot_bypass_auth(modules, name):
    from fastapi import Header, HTTPException
    module = modules[name]
    for value in (None, Header(default=None, alias="Authorization"), object()):
        with pytest.raises(HTTPException) as caught:
            module._require_service_token(value)
        assert caught.value.status_code == 401
    module._require_service_token("Bearer fixture-token")
    module.settings.service_token = ""
    with pytest.raises(HTTPException) as caught:
        module._require_service_token(Header(default=None, alias="Authorization"))
    assert caught.value.status_code == 503


def test_imported_parser_preserves_dates_and_source(modules, monkeypatch):
    module = modules["parser_normalizer"]
    async def audit(*args, **kwargs):
        pass
    monkeypatch.setattr(module, "emit_audit_event", audit)
    response = request(module, "/v1/parse/html", {
        "url": "https://example.org/article", "source": "fixture", "source_type": "news",
        "html": "<title>BTC event</title><p>Bitcoin was volatile.</p>",
        "metadata": {"updated_at": "2026-01-02T00:00:00Z"}})
    assert response.status_code == 200
    doc = response.json()["document"]
    assert doc["published_at"] is None
    assert doc["asset_tags"] == ["BTC"]
    assert doc["url"] == "https://example.org/article"
    assert doc["metadata"]["updated_at"] == "2026-01-02T00:00:00Z"


def test_browser_auth_is_separate_and_fail_closed(modules, monkeypatch):
    module = modules["gateway"]
    payload = {"asset": "BTC", "question": "Why?"}
    calls = []

    async def fake_chat(req, authorization):
        calls.append(authorization)
        return {"execution_disabled": True}

    monkeypatch.setattr(module, "chat", fake_chat)
    assert request(module, "/v1/browser/chat", payload).status_code == 503
    module.settings.browser_chat_token = "browser-fixture"
    for token in ("", "Bearer wrong", "Bearer fixture-token"):
        assert request(module, "/v1/browser/chat", payload, token).status_code == 401
    assert calls == []
    response = request(module, "/v1/browser/chat", payload, "Bearer browser-fixture")
    assert response.status_code == 200
    assert calls == ["Bearer fixture-token"]
    module.settings.browser_chat_token = "fixture-token"
    assert request(module, "/v1/browser/chat", payload).status_code == 503
    module.settings.browser_chat_token = "browser-fixture"
    module.settings.service_token = ""
    assert request(module, "/v1/browser/chat", payload, "Bearer browser-fixture").status_code == 503


def test_browser_page_never_embeds_credentials(modules, monkeypatch):
    module = modules["gateway"]
    module.settings.browser_chat_token = "browser-fixture"
    monkeypatch.setattr(module, "_load_structural_edge_shell_state", lambda: {})
    body = asyncio.run(module.chat_ui()).body.decode()
    assert "browser-fixture" not in body
    assert "fixture-token" not in body
    assert "fetch('/v1/browser/chat'" in body
    assert "'Authorization': 'Bearer ' + browserToken" in body
    assert "tokenInput.value = ''" in body
    assert "localStorage" not in body
    assert "sessionStorage" not in body
    assert body.index("if (!res.ok)") < body.index("data = await res.json()")
    assert "catch (error)" in body
    assert "Request failed. Check connection and gateway availability." in body
    for outcome in ("request not sent", "request refused", "request failed"):
        assert f"No answer metadata: {outcome}." in body


def test_keyword_retrieval_is_parameterized_and_labelled(modules, monkeypatch):
    from types import SimpleNamespace
    memory = modules["memory_retrieval"]
    calls = []
    row = {"id": 7, "title": "Bitcoin regulation", "url": "https://example.org/regulation",
           "source": "fixture", "lexical_rank": 0.2}
    def fetch(sql, params):
        if "AS lexical_rank" in sql:
            calls.append((sql, params))
            return [row]
        return []
    monkeypatch.setattr(memory.db, "fetch_all", fetch)
    monkeypatch.setattr(memory, "_qdrant_client", lambda: SimpleNamespace(search=lambda **kw: []))
    async def no_audit(*args, **kwargs):
        pass
    monkeypatch.setattr(memory, "emit_audit_event", no_audit)
    result = request(memory, "/v1/memory/retrieve", {"asset": "BTC", "question": "regulation", "limit": 100})
    assert result.status_code == 200
    data = result.json()
    assert data["lexical_matches"] == [row]
    assert data["vector_method"].endswith("not_semantic")
    sql, params = calls[0]
    assert params == ("regulation", "BTC", "regulation", 20)
    assert "fetched_at <= NOW()" in sql and "published_at <= NOW()" in sql
    assert "regulation" not in sql
    citations = modules["orchestrator"]._build_evidence({"get_signal_summary": data})
    citation = next(x for x in citations if x.get("document_id") == 7)
    assert citation["url"] == row["url"]
    assert citation["semantic_relevance_verified"] is False


def test_question_scaffolding_reaches_parameterized_search(modules, monkeypatch):
    from types import SimpleNamespace
    memory = modules["memory_retrieval"]
    captured = []
    def fetch(sql, params):
        if "AS lexical_rank" in sql:
            captured.append(params)
        return []
    async def no_audit(*args, **kwargs):
        pass
    monkeypatch.setattr(memory.db, "fetch_all", fetch)
    monkeypatch.setattr(memory, "_qdrant_client", lambda: SimpleNamespace(search=lambda **kw: []))
    monkeypatch.setattr(memory, "emit_audit_event", no_audit)
    original = "What news explains Bitcoin liquidations?"
    response = request(memory, "/v1/memory/retrieve", {"asset": "BTC", "question": original})
    assert response.status_code == 200
    assert response.json()["question"] == original
    assert response.json()["keyword_query"]["query"] == "Bitcoin liquidations"
    assert captured == [("Bitcoin liquidations", "BTC", "Bitcoin liquidations", 5)]


def test_signal_tool_forwards_actual_question(modules, monkeypatch):
    from shared import tools
    calls = []
    async def payload(method, url, **kwargs):
        calls.append(kwargs["payload"])
        return {"lexical_matches": [{"id": 7}], "retrieval_method": "english_keyword_full_text"}
    async def market(asset):
        return {}
    monkeypatch.setattr(tools, "_request_json", payload)
    monkeypatch.setattr(tools, "get_market_snapshot", market)
    result = asyncio.run(tools.get_signal_summary("BTC", question="regulation"))
    assert calls[0]["question"] == "regulation"
    assert result["lexical_matches"] == [{"id": 7}]


def test_archive_forwards_service_auth(modules, monkeypatch):
    module = modules["archive_lookup"]
    calls = []
    class Client:
        def __init__(self, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def post(self, url, **kwargs):
            calls.append(kwargs["headers"])
            import httpx
            return httpx.Response(200, json={"ok": True}, request=httpx.Request("POST", url))
    monkeypatch.setattr(module.httpx, "AsyncClient", Client)
    asyncio.run(module._parse_html("https://example.org", "fixture", "BTC"))
    asyncio.run(module._ingest_document({}))
    assert calls == [{"Authorization": "Bearer fixture-token"}] * 2
    module.settings.service_token = ""
    with pytest.raises(RuntimeError, match="service_auth_not_configured"):
        asyncio.run(module._ingest_document({}))
    assert len(calls) == 2


def test_missing_market_does_not_invent_a_price(modules):
    reasoning = modules["orchestrator"]._fallback_reasoning("BTC", "Why?", {})
    assert "unavailable" in reasoning["current_cause"]
    assert "trading up" not in reasoning["current_cause"]
    unavailable = {"ok": False, "price": None, "bid": None, "ask": None, "source": "unavailable"}
    assert modules["orchestrator"]._build_evidence({"get_market_snapshot": unavailable}) == []
