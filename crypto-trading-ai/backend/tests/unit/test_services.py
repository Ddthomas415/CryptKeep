from backend.app.schemas.research import ExplainRequest
from backend.app.services.research_service import explain


def test_explain_defaults_to_execution_disabled() -> None:
    out = explain(ExplainRequest(question="Why is SOL moving?", asset="SOL"))
    assert out.execution_disabled is True
    assert out.asset == "SOL"
