from pathlib import Path

def test_market_data_does_not_log_or_audit_raw_exception_text() -> None:
    text = Path("phase1_research_copilot/market_data/main.py").read_text()
    assert 'str(exc)' not in text
    assert '"error_type": type(exc).__name__' in text
