import asyncio

from services.gateway.routes import query as gateway_query
from services.orchestrator.workflows import explain_asset as wf
from shared.config import Settings
from shared.schemas.explain import ExplainRequest


class _DummyLogger:
    def info(self, *_args, **_kwargs):
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


async def _run_orchestrator_flow(monkeypatch):
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
        if "/news/" in url:
            return {
                "asset": "SOL",
                "items": [
                    {
                        "source": "newsapi",
                        "title": "SOL rises as active addresses climb",
                        "published_at": "2026-03-10T20:45:00Z",
                    },
                    {
                        "source": "newsapi",
                        "title": "Liquidity deepens in SOL pairs",
                        "published_at": "2026-03-10T20:55:00Z",
                    },
                ],
            }
        if "/archive/" in url:
            return {
                "asset": "SOL",
                "items": [
                    {
                        "source": "wayback",
                        "title": "Historical Solana roadmap milestone precedent",
                        "timestamp": "2025-03-10T21:00:00Z",
                    }
                ],
            }
        if url.endswith("/search"):
            return {
                "results": [
                    {
                        "title": "Upcoming SOL governance vote scheduled next week",
                        "timeline": "future",
                        "source": "newsapi_or_seed",
                    }
                ]
            }
        if "/risk/evaluate" in url:
            return {
                "execution_disabled": True,
                "approved": False,
                "reason": "Phase 1 research mode only",
            }
        if "/paper/positions" in url:
            return {
                "positions": [
                    {
                        "symbol": "SOL-USD",
                        "quantity": 1.25,
                        "avg_entry_price": 145.2,
                        "realized_pnl": 0.0,
                    }
                ]
            }
        if "/paper/fills" in url:
            return {
                "fills": [
                    {
                        "id": "930f6d38-07ca-4ced-8447-d6b0293adb2f",
                        "order_id": "d5955f0d-2455-404a-8cf5-e1468e407963",
                        "symbol": "SOL-USD",
                        "side": "buy",
                        "price": 145.2,
                        "quantity": 1.25,
                        "fee": 0.12,
                        "liquidity": "taker",
                        "created_at": "2026-03-10T21:00:01Z",
                    }
                ]
            }
        if "/audit/log" in url:
            return {"status": "ok"}
        if "/ingest/news" in url:
            return {"inserted": 2, "asset": "SOL"}
        raise AssertionError(f"unexpected_url:{url}")

    async def _fake_emit_audit(*, client, settings, request_id, event_type, message, payload=None, level="INFO"):
        _ = (client, settings, request_id, event_type, message, payload, level)
        return None

    async def _fake_polish_explanation(*, openai_api_key, model, draft, timeout=12.0):
        _ = (openai_api_key, model, timeout)
        return {
            "current_cause": draft["current_cause"],
            "past_precedent": draft["past_precedent"],
            "future_catalyst": draft["future_catalyst"],
        }

    monkeypatch.setattr(wf, "_request_with_retry", _fake_request_with_retry)
    monkeypatch.setattr(wf, "_emit_audit", _fake_emit_audit)
    monkeypatch.setattr(wf, "polish_explanation", _fake_polish_explanation)

    settings = Settings(
        market_data_url="http://market_data:8002",
        news_ingestion_url="http://news_ingestion:8003",
        archive_lookup_url="http://archive_lookup:8004",
        memory_url="http://memory:8006",
        risk_stub_url="http://risk_stub:8007",
        audit_log_url="http://audit_log:8008",
        openai_api_key="test",
    )
    _request_id, response = await wf.explain_asset_flow(
        settings=settings,
        logger=_DummyLogger(),
        question="Why is SOL moving?",
        asset="SOL",
    )
    return response


def test_orchestrator_happy_path_response(monkeypatch):
    response = asyncio.run(_run_orchestrator_flow(monkeypatch))

    assert response["asset"] == "SOL"
    assert response["question"] == "Why is SOL moving?"
    assert response["execution_disabled"] is True
    assert isinstance(response["paper_positions"], list)
    assert isinstance(response["recent_paper_fills"], list)
    assert isinstance(response["paper_risk_state"], dict)
    assert isinstance(response["confidence"], float)
    assert response["confidence"] > 0

    evidence_types = {item.get("type") for item in response.get("evidence", [])}
    assert "market" in evidence_types
    assert "document" in evidence_types


def test_gateway_query_explain_happy_path_contract(monkeypatch):
    async def _fake_call_orchestrator(payload):
        _ = payload
        return {
            "asset": "SOL",
            "question": "Why is SOL moving?",
            "current_cause": "Recent price expansion coincides with increased volume and relevant news mentions.",
            "past_precedent": "Historical roadmap announcements showed similar follow-through.",
            "future_catalyst": "A scheduled governance event remains pending.",
            "confidence": 0.78,
            "evidence": [
                {"type": "market", "source": "coinbase", "timestamp": "2026-03-10T21:00:00Z"},
                {"type": "document", "source": "newsapi", "title": "Sample headline"},
            ],
            "execution_disabled": True,
        }

    monkeypatch.setattr(gateway_query, "_call_orchestrator", _fake_call_orchestrator)

    req = ExplainRequest(asset="SOL", question="Why is SOL moving?")
    out = asyncio.run(gateway_query.explain(req))

    assert out.asset == "SOL"
    assert out.execution_disabled is True
    assert out.confidence == 0.78
    types = {ev.type for ev in out.evidence}
    assert "market" in types
    assert "document" in types
