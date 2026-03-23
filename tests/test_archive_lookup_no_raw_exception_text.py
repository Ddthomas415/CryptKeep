from pathlib import Path

def test_archive_lookup_does_not_log_or_audit_raw_exception_text() -> None:
    text = Path("phase1_research_copilot/archive_lookup/main.py").read_text()
    assert '"error": str(exc)' not in text
    assert '"error_type": type(exc).__name__' in text
