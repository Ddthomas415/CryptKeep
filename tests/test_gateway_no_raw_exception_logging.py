from pathlib import Path

def test_gateway_does_not_log_raw_exception_text() -> None:
    text = Path("phase1_research_copilot/gateway/main.py").read_text()
    assert 'str(exc)' not in text
    assert 'error_type' in text
