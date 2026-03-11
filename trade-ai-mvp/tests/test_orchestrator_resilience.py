import asyncio

from services.orchestrator.workflows import explain_asset as wf
from shared.config import Settings


class _DummyLogger:
    def info(self, *_args, **_kwargs):
        return None

    def warning(self, *_args, **_kwargs):
        return None


class _DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _DummyHttpx:
    AsyncClient = _DummyAsyncClient


def _settings() -> Settings:
    return Settings(
        market_data_url="http://market_data:8002",
        news_ingestion_url="http://news_ingestion:8003",
        archive_lookup_url="http://archive_lookup:8004",
        memory_url="http://memory:8006",
        risk_stub_url="http://risk_stub:8007",
        audit_log_url="http://audit_log:8008",
        openai_api_key="",
    )


def test_explain_flow_degrades_when_news_archive_memory_unavailable(monkeypatch):
    monkeypatch.setattr(wf, "httpx", _DummyHttpx)

    async def _fake_request_with_retry(*, client, method, url, json_payload=None, retries=2):
        _ = (client, method, json_payload, retries)
        if "/market/" in url and "/snapshot" in url:
            return {
                "symbol": "SOL-USD",
                "exchange": "coinbase",
                "last_price": "145.20",
                "bid": "145.10",
                "ask": "145.30",
                "spread": "0.20",
                "timestamp": "2026-03-10T21:00:00Z",
            }
        if "/risk/evaluate" in url:
            return {"execution_disabled": True, "approved": False, "reason": "Phase 1 research mode only"}
        if "/ingest/news" in url or "/news/" in url or "/archive/" in url or url.endswith("/search"):
            raise RuntimeError("dependency_unavailable")
        if "/audit/log" in url:
            return {"status": "ok"}
        raise AssertionError(f"unexpected_url:{url}")

    async def _fake_emit_audit(*, client, settings, request_id, event_type, message, payload=None, level="INFO"):
        _ = (client, settings, request_id, event_type, message, payload, level)
        return None

    async def _fake_polish_explanation(*, openai_api_key, model, draft, timeout=12.0):
        _ = (openai_api_key, model, draft, timeout)
        return None

    monkeypatch.setattr(wf, "_request_with_retry", _fake_request_with_retry)
    monkeypatch.setattr(wf, "_emit_audit", _fake_emit_audit)
    monkeypatch.setattr(wf, "polish_explanation", _fake_polish_explanation)

    _request_id, response = asyncio.run(
        wf.explain_asset_flow(
            settings=_settings(),
            logger=_DummyLogger(),
            question="Why is SOL moving?",
            asset="SOL",
        )
    )

    assert response["asset"] == "SOL"
    assert response["execution_disabled"] is True
    assert response["confidence"] == 0.55
    assert response["past_precedent"].startswith("No strong historical precedent")
    assert response["future_catalyst"].startswith("No future catalyst found")
    evidence_types = {item.get("type") for item in response.get("evidence", [])}
    assert evidence_types == {"market"}


def test_explain_flow_defaults_to_execution_disabled_when_risk_unavailable(monkeypatch):
    monkeypatch.setattr(wf, "httpx", _DummyHttpx)

    async def _fake_request_with_retry(*, client, method, url, json_payload=None, retries=2):
        _ = (client, method, json_payload, retries)
        if "/market/" in url and "/snapshot" in url:
            return {
                "symbol": "SOL-USD",
                "exchange": "coinbase",
                "last_price": "145.20",
                "bid": "145.10",
                "ask": "145.30",
                "spread": "0.20",
                "timestamp": "2026-03-10T21:00:00Z",
            }
        if "/ingest/news" in url:
            return {"inserted": 1, "asset": "SOL"}
        if "/news/" in url:
            return {
                "asset": "SOL",
                "items": [
                    {"source": "newsapi", "title": "SOL liquidity expands", "published_at": "2026-03-10T20:55:00Z"}
                ],
            }
        if "/archive/" in url:
            return {
                "asset": "SOL",
                "items": [{"source": "wayback", "title": "Past SOL cycle precedent", "timestamp": "2025-03-10T21:00:00Z"}],
            }
        if url.endswith("/search"):
            return {"results": [{"title": "Upcoming SOL governance vote", "timeline": "future", "source": "seed"}]}
        if "/risk/evaluate" in url:
            raise RuntimeError("risk_stub_down")
        if "/audit/log" in url:
            return {"status": "ok"}
        raise AssertionError(f"unexpected_url:{url}")

    async def _fake_emit_audit(*, client, settings, request_id, event_type, message, payload=None, level="INFO"):
        _ = (client, settings, request_id, event_type, message, payload, level)
        return None

    async def _fake_polish_explanation(*, openai_api_key, model, draft, timeout=12.0):
        _ = (openai_api_key, model, draft, timeout)
        return None

    monkeypatch.setattr(wf, "_request_with_retry", _fake_request_with_retry)
    monkeypatch.setattr(wf, "_emit_audit", _fake_emit_audit)
    monkeypatch.setattr(wf, "polish_explanation", _fake_polish_explanation)

    _request_id, response = asyncio.run(
        wf.explain_asset_flow(
            settings=_settings(),
            logger=_DummyLogger(),
            question="Why is SOL moving?",
            asset="SOL",
        )
    )

    assert response["asset"] == "SOL"
    assert response["execution_disabled"] is True
    assert response["confidence"] == 0.75
    evidence_types = {item.get("type") for item in response.get("evidence", [])}
    assert "market" in evidence_types
    assert "document" in evidence_types
    assert "archive" in evidence_types


def test_explain_flow_returns_local_fallback_when_httpx_missing(monkeypatch):
    monkeypatch.setattr(wf, "httpx", None)

    _request_id, response = asyncio.run(
        wf.explain_asset_flow(
            settings=_settings(),
            logger=_DummyLogger(),
            question="Why is SOL moving?",
            asset="SOL",
        )
    )

    assert response["asset"] == "SOL"
    assert response["execution_disabled"] is True
    assert response["confidence"] == 0.55
    assert isinstance(response["evidence"], list)
