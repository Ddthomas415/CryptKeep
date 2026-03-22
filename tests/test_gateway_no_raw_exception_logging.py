from pathlib import Path

def test_gateway_does_not_log_raw_exception_text() -> None:
    text = Path("phase1_research_copilot/gateway/main.py").read_text()
    assert 'extra={"context": {"error": str(exc)}}' not in text
    assert 'extra={"context": {"asset": explain_payload.get("asset"), "error": str(exc)}}' not in text
    assert 'error_type' in text
