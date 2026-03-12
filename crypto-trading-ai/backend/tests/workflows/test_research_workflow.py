from types import SimpleNamespace

from backend.app.api.routes.research import research_explain, research_search
from backend.app.schemas.research import ExplainRequest, SearchRequest


class DummyRequest(SimpleNamespace):
    pass


def test_research_explain_workflow_success() -> None:
    req = DummyRequest(state=SimpleNamespace(request_id="req_workflow_1"))
    payload = research_explain(
        ExplainRequest(
            question="Why is SOL moving?",
            asset="SOL",
            filters={"timelines": ["past", "present", "future"]},
        ),
        req,
    )
    assert payload["status"] == "success"
    assert payload["data"]["execution_disabled"] is True


def test_research_search_workflow_success() -> None:
    req = DummyRequest(state=SimpleNamespace(request_id="req_workflow_2"))
    payload = research_search(
        SearchRequest(query="SOL", page=1, page_size=10),
        req,
    )
    assert payload["status"] == "success"
    assert "items" in payload["data"]
    assert payload["meta"]["page"] == 1
