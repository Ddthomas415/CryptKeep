from types import SimpleNamespace

from backend.app.api.routes.dashboard import dashboard_summary
from backend.app.api.routes.research import research_explain
from backend.app.schemas.research import ExplainRequest


class DummyRequest(SimpleNamespace):
    pass


def test_dashboard_summary_returns_standard_envelope() -> None:
    req = DummyRequest(state=SimpleNamespace(request_id="req_test_1"))
    payload = dashboard_summary(req)
    assert set(payload.keys()) == {"request_id", "status", "data", "error", "meta"}
    assert payload["status"] == "success"
    assert payload["error"] is None


def test_research_explain_contains_required_fields() -> None:
    req = DummyRequest(state=SimpleNamespace(request_id="req_test_2"))
    payload = research_explain(
        ExplainRequest(question="Why is SOL moving?", asset="SOL"),
        req,
    )
    data = payload["data"]
    required = {
        "asset",
        "question",
        "current_cause",
        "past_precedent",
        "future_catalyst",
        "confidence",
        "risk_note",
        "execution_disabled",
        "evidence",
    }
    assert required.issubset(set(data.keys()))
