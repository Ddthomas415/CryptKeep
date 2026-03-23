from pathlib import Path

def test_audit_client_does_not_log_raw_exception_text() -> None:
    text = Path("phase1_research_copilot/shared/audit.py").read_text()
    assert '"error": str(exc)' not in text
    assert '"error_type": type(exc).__name__' in text
